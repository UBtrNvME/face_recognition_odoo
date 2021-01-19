import os
from collections import namedtuple
from logging import getLogger

from odoo import api, fields, models
from odoo.tools import date_utils as dateutil

from ..services.img_manipulation import base64_to_binary, binary_to_base64

SUCCESS = 900
ERROR = 1000
PNID_POSSIBLE_MIMETYPES = ["application/pdf", "image/jpeg", "image/png"]

NextcloudAgentResponse = namedtuple(
    "NextcloudAgentResponse", ["success", "code", "message", "result"]
)
NextcloudFileInfo = namedtuple("NextcloudFileInfo", ["path", "mimetype"])

KEY_FOR_NEXTCLOUD_HOST = "nextcloud_connector.nextcloud_host_url"

_logger = getLogger(__name__)


class NextcloudAgent(models.TransientModel):
    _name = "cad.nextcloud.agent"

    user_id = fields.Integer(string="Odoo user id")
    login = fields.Char(string="User Login")
    password = fields.Char(string="User Password")
    nextcloud_uid = fields.Char(string="Nextcloud UID")
    _WRAPPER = None

    def _get_api_wrapper(self, login, password):
        host = (
            self.env["ir.config_parameter"]
            .search([("key", "=", KEY_FOR_NEXTCLOUD_HOST)])
            .value
        )

        return self.env["nextcloud.wrapper"].construct_wrapper(host, login, password)

    def wrap(self, login, password):
        return self._get_api_wrapper(login, password)

    @property
    def WRAPPER(self):
        return self.wrap(self.login, self.password)

    @WRAPPER.setter
    def WRAPPER(self, value):
        self._WRAPPER = value

    @WRAPPER.deleter
    def WRAPPER(self):
        del self._WRAPPER

    def who_am_i(self):
        users = self.WRAPPER.get_users().data["users"]
        for user in users:
            info = self.WRAPPER.get_user(user)
            if info and info.data["email"] and info.data["email"] == self.login:
                return user
        return ""

    @api.model
    def with_user_(self, user, display_name=True):
        # TODO: In future have to optimize this code, to use less repeating code
        if display_name:
            user_credentials = self.env["nextcloud.user_credential"].search(
                [("display_name", "=", user)]
            )
            if user_credentials:
                login, password = user_credentials.decrypt_credentials()
            else:
                return None
        else:
            user_credentials = self.env["nextcloud.user_credential"].search(
                [("user_id", "=", user)]
            )
            if user_credentials:
                login, password = user_credentials.decrypt_credentials()
            else:
                return None
        return self.create(
            [
                {
                    "login": login,
                    "password": password,
                    "nextcloud_uid": user_credentials.nextcloud_uid,
                    "user_id": user_credentials.user_id,
                }
            ]
        )

    @api.model
    def sudo_(self):
        IrConfigParameter = self.env["ir.config_parameter"]
        nextcloud_super_user_login = IrConfigParameter.get_param(
            "nextcloud_connector.super_user_login"
        )
        nextcloud_super_user_password = IrConfigParameter.get_param(
            "nextcloud_connector.super_user_password"
        )
        if nextcloud_super_user_login and nextcloud_super_user_password:
            return self.create(
                {
                    "login": nextcloud_super_user_login,
                    "password": nextcloud_super_user_password,
                    "nextcloud_uid": "Aitemir",
                }
            )
        # In case that system has not been provided
        # with super user credentials return None
        return None

    def upload_file(self, filebytes, remote_filepath, timestamp):
        if self.nextcloud_uid:
            try:
                self.WRAPPER.upload_file_contents(
                    self.nextcloud_uid,
                    file_contents=filebytes,
                    remote_filepath=remote_filepath,
                    timestamp=timestamp,
                )
                return NextcloudAgentResponse(
                    True, SUCCESS, "Successfully uploaded file", False
                )
            except:
                return NextcloudAgentResponse(
                    False, ERROR, "Error uploading file", False
                )

    def download_file(self, path):
        if self.nextcloud_uid:
            try:
                res = self.WRAPPER.get_file_content(self.nextcloud_uid, path)
                return NextcloudAgentResponse(
                    True, SUCCESS, "Successfully downloaded file", res
                )
            except:
                return NextcloudAgentResponse(
                    True, ERROR, "Error downloading file", False
                )

    def list_folders(self, path, depth=None, all_properties=True):
        if self.nextcloud_uid:
            try:
                result = self.WRAPPER.list_folders(
                    self.nextcloud_uid,
                    path=path,
                    depth=depth,
                    all_properties=all_properties,
                )
                return NextcloudAgentResponse(
                    True, SUCCESS, "Successfully listed folders", result.data
                )
            except:
                return NextcloudAgentResponse(
                    True, ERROR, "Error listing Folders", False
                )

    def create_folder(self, folder_path):
        if self.nextcloud_uid:
            try:
                result = self.WRAPPER.create_folder(
                    uid=self.nextcloud_uid, folder_path=folder_path
                )
                return NextcloudAgentResponse(
                    True, SUCCESS, "Successfully created folder", None
                )
            except:
                return NextcloudAgentResponse(
                    True, ERROR, "Error creating folder", None
                )

    def set_favorites(self, path):
        if self.nextcloud_uid:
            return self.WRAPPER.set_favorites(self.nextcloud_uid, path)

    @api.model
    def create(self, values):
        agent = super().create(values)
        return agent

    @api.model
    def _cron_job_download(self):
        sudo_user = self.sudo_()
        IrConfigParameter = self.env["ir.config_parameter"]
        CadDiagram = self.env["cad.diagram"].sudo()
        src = IrConfigParameter.get_param("cad.nextcloud_parse_source", "")
        tree = sudo_user.list_folders(src).result
        not_visited = [item for i, item in enumerate(tree) if item["favorite"] == "0"]
        len_root_folder = len(not_visited.pop(0)["href"].split("/")) - 1
        if len(not_visited):
            _logger.info("Starting Job `Autopull from Nextcloud (CAD)`")
            user_related = {}
            for item in not_visited:
                user_name = item["owner_display_name"]
                if user_name in user_related:
                    user_related[user_name].append(
                        NextcloudFileInfo(
                            os.path.join(
                                "/", *item["href"].split("/")[len_root_folder - 1 :]
                            ),
                            item["content_type"],
                        )
                    )
                else:
                    user_related[user_name] = [
                        NextcloudFileInfo(
                            os.path.join(
                                "/", *item["href"].split("/")[len_root_folder - 1 :]
                            ),
                            item["content_type"],
                        )
                    ]

            for user, files in user_related.items():
                _user = self.with_user_(user, display_name=True)
                if not _user:
                    _logger.warning(
                        (
                            "Nextcloud user with display name `%s` "
                            "cannot be found in the database, "
                            "thus perform skipping"
                        )
                        % user
                    )
                    continue
                for file in files:
                    if file.mimetype in PNID_POSSIBLE_MIMETYPES:
                        file_name = file.path.split("/")[-1]

                        response = _user.download_file(file.path)
                        if response.code == SUCCESS:
                            filebytes = response.result.data
                            base64encoded = binary_to_base64(filebytes)
                            diagram = CadDiagram.with_user(_user.user_id).create(
                                {
                                    "name": file_name,
                                    "attachment": base64encoded,
                                    "nextcloud_path": file.path,
                                    "diagram_type": "pandid",
                                    "state": "unsync",
                                }
                            )
                            diagram.delayed_task()
                            sudo_user.set_favorites(file.path)
            _logger.info("Done Job `Autopull from Nextcloud (CAD)`")
        else:
            _logger.info("Skipping Job `Autopull from Nextcloud (CAD)`")

    @api.model
    def _cron_job_upload(self):
        unsynced_diagrams = self.env["cad.diagram"].search([("state", "=", "unsync")])
        IrConfigParameter = self.env["ir.config_parameter"]
        dst = IrConfigParameter.get_param("cad.nextcloud_parse_destination", "")
        src = IrConfigParameter.get_param("cad.nextcloud_parse_source", "")
        if unsynced_diagrams:
            _logger.info("Starting Job `Upload P&IDs to Nextcloud`")
            for diagram in unsynced_diagrams:
                json_data_filebytes = diagram.content_data.encode("utf-8")
                resulting_image_filebytes = base64_to_binary(diagram.image_1920)
                user_agent = self.with_user_(diagram.create_uid.id, False)
                new_folder = os.path.join(diagram.nextcloud_path.replace(src, dst))
                user_agent.create_folder(new_folder)
                user_agent.upload_file(
                    json_data_filebytes,
                    new_folder + "/data.json",
                    int(dateutil.datetime.now().timestamp()),
                )
                user_agent.upload_file(
                    resulting_image_filebytes,
                    new_folder + "/p&id.png",
                    int(dateutil.datetime.now().timestamp()),
                )
                diagram.state = "sync"
            _logger.info("Done Job `Upload P&IDs to Nextcloud`")
        else:
            _logger.info("Skipping Job `Upload P&IDs to Nextcloud`")

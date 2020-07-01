import tkinter

import PIL.Image
import PIL.ImageTk
import cv2
import locale
locale.setlocale(locale.LC_NUMERIC, 'C')

class App:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.attributes("-topmost", True)
        self.window.title(window_title)
        self.video_source = video_source

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)
        self.number_of_pictures_taken = 0
        self.number_of_pictures_taken_lbl = tkinter.Label(window,
                                                          text="Pictures taken " + str(self.number_of_pictures_taken))
        self.number_of_pictures_taken_lbl.pack(side="top")

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        # Button that lets the user take a snapshot
        self.btn_snapshot = tkinter.Button(window, text="Snapshot", width=50, command=self.append_snapshot_in64base)
        self.btn_snapshot.pack(anchor=tkinter.CENTER, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()
        self.snapshotes_in64base = []
        self.window.mainloop()

    def append_snapshot_in64base(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            self.snapshotes_in64base.append(cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)))
            self.number_of_pictures_taken += 1
            self.number_of_pictures_taken_lbl["text"] = "Pictures taken " + str(self.number_of_pictures_taken)

    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

        self.window.after(self.delay, self.update)


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


# Create a window and pass it to the Application object
# photobooth = App(tkinter.Tk(), "Tkinter and OpenCV")


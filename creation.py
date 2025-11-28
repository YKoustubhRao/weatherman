import matplotlib.pyplot as plt
import shapefile
import argparse


class PolygonDigitizer:
    def __init__(self):
        self.fig, self.ax = plt.subplots()

        # Try loading a background earth map
        try:
            img = plt.imread("worldmap.jpg")
            self.ax.imshow(img, extent=[-180, 180, -90, 90], zorder=0)
        except Exception as e:
            print("Could not load worldmap.jpg:", e)

        self.ax.set_title("Click to add points. Press Enter to finish polygon.")
        self.ax.set_xlim([-180, 180])
        self.ax.set_ylim([-90, 90])
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")

        # State
        self.current_points = []
        self.all_polygons = []
        self.polygon_finished = False  # Flag set when Enter pressed

        # Connect events
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        x, y = event.xdata, event.ydata
        self.current_points.append((x, y))

        # Draw point
        self.ax.plot(x, y, "ro", zorder=10)

        # Draw edge from previous point
        if len(self.current_points) > 1:
            xs = [self.current_points[-2][0], self.current_points[-1][0]]
            ys = [self.current_points[-2][1], self.current_points[-1][1]]
            self.ax.plot(xs, ys, "-r", zorder=10)

        self.fig.canvas.draw()

    def on_key(self, event):
        # Only signal. No input() here!
        if event.key == "enter":
            self.polygon_finished = True


def save_shapefile(polygons, filename="output"):
    writer = shapefile.Writer(filename, shapeType=shapefile.POLYGON)
    writer.autoBalance = 1
    writer.field("name", "C")

    for name, pts in polygons:
        writer.record(name)
        writer.poly([pts])

    writer.close()

    prj = (
        'GEOGCS["WGS 84",DATUM["WGS_1984",'
        'SPHEROID["WGS 84",6378137,298.257223563]],'
        'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
    )
    with open(filename + ".prj", "w") as f:
        f.write(prj)

    print(f"\nSaved shapefile as {filename}.shp/.shx/.dbf/.prj")


def run():
    parser = argparse.ArgumentParser(description="View or Create shape files.")
    parser.add_argument(
        "--output", type=str, help="Filepath for the shapes to be dumped to."
    )
    parser.add_argument(
        "--input", type=str, help="Filepath for the shapes to be loaded from."
    )
    args = parser.parse_args()

    if args.output:
        digitizer = PolygonDigitizer()

        print("Instructions:")
        print(" - Click on map to add vertices.")
        print(" - Press Enter inside map window to close polygon.")
        print(" - Terminal will then ask for polygon name.")
        print(" - Type 'save' in terminal when done.\n")

        plt.show(block=False)

        while True:
            plt.pause(0.1)  # allow matplotlib to process GUI events

            # User pressed Enter inside the figure
            if digitizer.polygon_finished:
                digitizer.polygon_finished = False

                if not digitizer.current_points:
                    print("No points collected.")
                    continue

                print("Points collected:", digitizer.current_points)
                name = input("Enter polygon name: ").strip()
                digitizer.all_polygons.append((name, digitizer.current_points))

                # Draw closed polygon in blue
                xs = [p[0] for p in digitizer.current_points] + [
                    digitizer.current_points[0][0]
                ]
                ys = [p[1] for p in digitizer.current_points] + [
                    digitizer.current_points[0][1]
                ]
                digitizer.ax.plot(xs, ys, "-b", linewidth=2, zorder=15)

                # Remove all red "live" lines from previous polygon
                for ln in list(digitizer.ax.lines):
                    if ln.get_color() == "r":
                        ln.remove()  # safe in modern Matplotlib

                digitizer.current_points = []
                digitizer.fig.canvas.draw()
                continue

            # Terminal command interface
            cmd = input("Type 'save' to finish or Enter to continue: ").strip().lower()
            if cmd == "save":
                save_shapefile(digitizer.all_polygons, args.output)
                print("Done.")
                break
    else:
        print("Reading shapes from", args.input)


if __name__ == "__main__":
    run()

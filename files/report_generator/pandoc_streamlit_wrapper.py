from common.utils import *
import os
from matplotlib import pyplot as plt

class PandocStreamlitWrapper:

    def __init__(self, base_dir="/tmp"):
        self.md_lines = []
        self.report_dir = self.__create_report_dir(base_dir)

        self.image_index = 0
        self.plot_index = 0

        self.hyperlink_map = {}

    def generate_markdown_report(self):
        report_filename = os.path.join(self.report_dir, "report.md")

        self.md_lines = self.__draw_introduction()

        with open(report_filename, "w") as md_report:
            data = "  \n\n".join(self.md_lines)

            # removes non-standard characters
            data = data.encode('ascii', 'ignore').decode('ascii')
            md_report.write(data)

        return self.report_dir

    def __draw_introduction(self):
        intro_lines = []
        intro_lines.append('# CoViD-19 Risk Calculator')

        return intro_lines + self.md_lines

    def __create_report_dir(self, base_dir):
        unique_id = get_unique_id()
        report_dir = os.path.join(base_dir, "report_generator" + unique_id)
        os.makedirs(report_dir, exist_ok=True)

        return report_dir

    def wrapper_get_lines(self):
        return self.md_lines

    def markdown(self, body, unsafe_allow_html=False):
        self.md_lines.append(body)

    # this method is not part of the streamlit interface
    def markdown_hyperlink(self, body, resource_display_name, resource_link):
        self.md_lines.append(body)

        assert resource_display_name not in self.hyperlink_map
        self.hyperlink_map[resource_display_name] = resource_link

    # this method is not part of the streamlit interface
    def get_hyperlink_map(self):
        return self.hyperlink_map

    def write(self, *args, **kwargs):
        self.md_lines.extend(args)

    def text(self, *args, **kwargs):
        self.md_lines.extend(args)


    def pyplot(self, fig=None, clear_figure=True, **kwargs):

        # code partially taken from streamlit pyplot implementation

        if fig is None:
            fig = plt

        options = {"dpi": 200, "format": "png"}

        options = {a: kwargs.get(a, b) for a, b in options.items()}
        # Merge options back into kwargs.
        kwargs.update(options)

        image_name = f"plot_{self.plot_index}.png"
        self.plot_index += 1
        image_filename = os.path.join(self.report_dir, image_name)

        fig.savefig(image_filename, **kwargs)

        self.md_lines.append(f"![]({image_filename})")

    def image(self, *args, **kwargs):

        if isinstance(args[0], list):
            captions = kwargs.get("caption", ["" for i in range(len(args[0]))])
            table = self.__generate_table(args[0], captions)
            self.md_lines.append(table)
        else:
            table = self.__generate_mono_table(args[0])
            self.md_lines.append(table)

    def __generate_mono_table(self, image):
        image_name = f"image_{self.image_index}.png"
        self.image_index += 1
        image_filename = os.path.join(self.report_dir, image_name)

        image.save(image_filename)

        return self.__draw_mono_table(image_name)

    def __draw_mono_table(self, image_filename):
        return f"![]({image_filename}){{ width=250px }}  |\n"


    def __generate_table(self, images, captions):

        base_image_name = f"image_row_{self.image_index}"
        self.image_index += 1

        row_index = 0

        image_filenames = []

        for image in images:
            image_name = base_image_name + f"_{row_index}.png"
            row_index += 1

            image_filename = os.path.join(self.report_dir, image_name)
            image.save(image_filename)

            image_filenames.append(image_name)

        return self.__draw_image_table(image_filenames, captions)

    def __draw_image_table(self, img_fns, captions):

        table = "--             |  --         \n" \
                ":-------------------------:|:-------------------------:|\n"

        for i in range(0, len(img_fns) - 1, 2):

            image_left = img_fns[i]
            image_right = img_fns[i + 1]

            caption_left = captions[i]
            captions_right = captions[i + 1]

            table += f'![]({image_left}){{ width=150px }}  |  ![]({image_right}){{ width=150px }} |  \n' \
                     f'{caption_left}              | {captions_right}  | \n'

        if len(img_fns) % 2 == 1:
            table += f'![]({img_fns[-1]}){{ width=150px }}  |   |  \n' \
                     f'{captions[-1]}              |   | \n'

        table += '\n'

        return table

    def header(self, text):

        self.md_lines.append(f"## {text}")
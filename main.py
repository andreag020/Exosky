import os
import xml.etree.ElementTree as ET
import math
import plotly.graph_objects as go
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush

class MainWindow(QMainWindow):
    def __init__(self, xml_folder):
        super().__init__()
        self.xml_folder = xml_folder
        self.constelaciones = []  # List of constellations (names)
        self.buttons = []  # Store buttons for future management
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Select a Constellation")

        # Set a fixed size for the window
        self.setFixedSize(900, 700)

        # Load the background image using QPixmap and QPalette (scale it and avoid repetition)
        oImage = QPixmap("images/spacebackground.jpg")  # Ensure the path is correct
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
        self.setPalette(palette)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add margins and spacing for a cleaner layout
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create a layout for the buttons
        self.button_layout = QVBoxLayout()
        self.button_layout.setAlignment(Qt.AlignTop)

        # Load the constellations (names) and dynamically generate buttons
        self.load_constellations()
        self.generate_buttons()

        # Add the button layout inside a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_widget = QWidget()
        scroll_area_widget.setLayout(self.button_layout)
        scroll_area.setWidget(scroll_area_widget)
        layout.addWidget(scroll_area)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def load_constellations(self):
        """Load the names of the constellations from XML files."""
        for xml_file in os.listdir(self.xml_folder):
            if xml_file.endswith('.xml'):
                name = self.get_name_from_xml(os.path.join(self.xml_folder, xml_file))
                if name:
                    self.constelaciones.append({'name': name, 'path': os.path.join(self.xml_folder, xml_file)})

    def generate_buttons(self):
        """Generate buttons for each constellation."""
        # Create buttons for the loaded constellations
        for constelacion in self.constelaciones:
            button = QPushButton(constelacion['name'])
            button.setFixedSize(250, 50)  # Set a fixed size for the buttons
            button.setStyleSheet("""
                QPushButton {
                    background-color: #6C63FF;
                    color: white;
                    font-size: 16px;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #5A54E6;
                }
            """)
            button.clicked.connect(lambda checked, path=constelacion['path']: self.show_details_window(path))

            # Add a horizontal box layout to center each button
            hbox = QHBoxLayout()
            hbox.addStretch(1)
            hbox.addWidget(button)
            hbox.addStretch(1)

            self.button_layout.addLayout(hbox)
            self.buttons.append(button)

    def get_name_from_xml(self, xml_path):
        """Extract the name of the constellation from the XML file."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            name_element = root.find('name')
            if name_element is not None:
                return name_element.text
            else:
                print(f"No <name> tag found in {xml_path}")
        except Exception as e:
            print(f"Error reading the file {xml_path}: {e}")
        return None

    def show_details_window(self, xml_path):
        """Open a window showing details of the selected XML and draw the constellation."""
        constellation_data = self.extract_constellation_data(xml_path)
        if constellation_data:
            self.draw_constellation(constellation_data)

    def extract_constellation_data(self, xml_path):
        """Extract relevant data from the XML file for visualization."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            constellation = []
            name = root.find('name').text
            right_ascension = root.find('rightascension').text
            declination = root.find('declination').text
            distance = float(root.find('distance').text)

            constellation.append({
                'name': name,
                'rightascension': right_ascension,
                'declination': declination,
                'distance': distance
            })
            return constellation

        except Exception as e:
            print(f"Error extracting data from {xml_path}: {e}")
            return None

    def convert_to_cartesian(self, right_ascension, declination, distance):
        """Convert right ascension, declination, and distance to Cartesian coordinates."""
        ra_h, ra_m, ra_s = map(float, right_ascension.split())
        dec_d, dec_m, dec_s = map(float, declination.split())

        ra_degrees = 15 * (ra_h + ra_m / 60 + ra_s / 3600)
        sign = -1 if dec_d < 0 else 1
        dec_degrees = sign * (abs(dec_d) + dec_m / 60 + dec_s / 3600)

        ra_radians = math.radians(ra_degrees)
        dec_radians = math.radians(dec_degrees)

        x = distance * math.cos(dec_radians) * math.cos(ra_radians)
        y = distance * math.cos(dec_radians) * math.sin(ra_radians)
        z = distance * math.sin(dec_radians)

        return x, y, z

    def draw_constellation(self, constellation):
        """Draw the 3D representation of the constellation and include Earth."""
        x_vals, y_vals, z_vals, names = [], [], [], []

        # Convert each star's coordinates and store for plotting
        for star in constellation:
            x, y, z = self.convert_to_cartesian(star['rightascension'], star['declination'], star['distance'])
            x_vals.append(x)
            y_vals.append(y)
            z_vals.append(z)
            names.append(star['name'])

        # Create the 3D scatter plot for stars
        fig = go.Figure(data=[go.Scatter3d(
            x=x_vals, y=y_vals, z=z_vals,
            mode='markers',
            marker=dict(size=5, color=z_vals, colorscale='Viridis'),
            text=names,
            name='Stars'
        )])

        # Add Earth at the center of the system (0, 0, 0)
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],  # Coordinates for Earth
            mode='markers',
            marker=dict(size=10, color='blue'),  # Represent Earth in blue
            text=["Earth"],
            name='Earth'
        ))

        # Customize the 3D plot layout
        fig.update_layout(
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            ),
            title='3D Map of the Constellation and Earth',
            showlegend=True
        )

        fig.show()

# Initialize the application
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Create the main window and pass the folder with XML files
    main_window = MainWindow('BaseDatos/systems')
    main_window.show()

    sys.exit(app.exec_())

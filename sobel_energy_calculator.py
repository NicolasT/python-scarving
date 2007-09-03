from energy_calculator import EnergyCalculator
from scipy.ndimage.filters import generic_gradient_magnitude, sobel
import sys
from PIL import Image

class SobelEnergyCalculator(EnergyCalculator):
        def __init__(self, image):
                EnergyCalculator.__init__(self, image)

        def calculate_per_pixel(self):
                return False

        def _calculate_full_energy(self):
                return generic_gradient_magnitude(self.get_image_matrix(), derivative = sobel)

def usage(pname):
        print "Usage: %s filename.jpg" % pname

def main():
        image = None
        try:
                image = Image.open(sys.argv[-1])
        except:
                usage(sys.argv[0])
                return

        ec = SobelEnergyCalculator(image)
        energy = ec.get_energy_image()
        energy.show()

if __name__ == "__main__":
        try:
                try:
                        import cProfile as profile
                except ImportError:
                        import profile
        except ImportError:
                print "Not profiling"
                main()
                sys.exit()
        print "Profiling using %s" % profile.__name__
        profile.run("main()")

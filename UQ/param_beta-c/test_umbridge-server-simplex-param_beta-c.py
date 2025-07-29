# first, run the server as: python3 umbridge-server-simplex-param_beta-c.py
# run this script as:       python3 test_umbridge-server-simplex-param_beta-c.py http://localhost:4242  

import argparse
import umbridge

parser = argparse.ArgumentParser(description='Minimal HTTP model demo.')
parser.add_argument('url',metavar='url',type=str,
                    help='the URL on which the model is running, for example http://localhost:4242')
args = parser.parse_args()
print(f"Connecting to host URL {args.url}")

# Set up a model by connecting to URL
model = umbridge.HTTPModel(args.url,"forward")

#test get input method
output = model.get_input_sizes()
print(output)

#test get output method
output = model.get_output_sizes()
print(output)


#test model output
param = [[75.0, 10.0]]
output = model(param)
print(output)


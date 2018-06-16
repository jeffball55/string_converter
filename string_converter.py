# This script uses z3 to determine how to add 2 integers together to get a desired value (as a number or string)
import sys, argparse, binascii
import z3

##########################################################################################
# A portable version that can be used in exploits ########################################
##########################################################################################

def get_values(desired_value, operation = "add"):
	BAD_CHARS = range(0, 0x30)
	BAD_CHARS.append(ord("#"))
	BAD_CHARS.append(ord("?"))

	xs = []
	ys = []

	s = z3.Solver()
	x = z3.BitVec('x', 32)
	y = z3.BitVec('y', 32)

	if operation.lower() == "xor":
		s.append(x ^ y == desired_value)
	elif operation.lower() == "subtract":
		s.append(x - y == desired_value)
	else:
		s.append(x + y == desired_value)

	for i in range(0, 4):
		xchar = z3.Extract(((i + 1) * 8) - 1, i * 8, x)
		ychar = z3.Extract(((i + 1) * 8) - 1, i * 8, y)
		for j in BAD_CHARS:
			s.append(xchar != j)
			s.append(ychar != j)

	result = s.check()
	if result == z3.sat:
		model = s.model()
		xs.append(model.eval(x).as_long())
		ys.append(model.eval(y).as_long())
		combined = (xs[-1] + ys[-1]) & 0xffffffff
		print "x = 0x{:x} y = 0x{:x} combined = 0x{:x} ({})".format(xs[-1], ys[-1], combined, binascii.unhexlify("{:08x}".format(combined)))
	else:
		print result
		print s.to_smt2()

	return xs[0], ys[0]


##########################################################################################
# Parse and convert the arguments ########################################################
##########################################################################################

parser = argparse.ArgumentParser(description="Convert a string into two halves that can be recombined with math")
parser.add_argument('value', type=str, default=None, help='String or hex value to convert')
parser.add_argument('-bad_chars', type=str, help='A list of bad characters (hexstring).  Default is [0,0x2f] and "?"')
parser.add_argument('-operation', type=str, default="add", help='The combining operation (add|subtract|xor)')
parser.add_argument('-big_endian', required=False, action='store_true', help="Whether the architecture is big endian or not")
parser.add_argument('-is_hex', required=False, action='store_true', help='Whether the value is a hex value and not a string')
parser.add_argument('-strip_space', required=False, action='store_true', help='Call python strip() on the ' + 
	' value (works around the python bug where the value starts with a dash ("-"))')
args = parser.parse_args()

BAD_CHARS = []
if args.bad_chars != None:
	BAD_CHARS = binascii.unhexlify(args.bad_chars)
else:
	BAD_CHARS = range(0, 0x30)
	BAD_CHARS.append(ord("?"))

# Parse the arguments to get the value(s) we want to add to
rounds = []
if args.is_hex:
  rounds.append(int(args.value, 16))
else:
  value = args.value
  if args.strip_space:
    value = value.strip()
  while len(value) != 0:
    round_arg = value[0:4] 
    value = value[4:]
    while len(round_arg) < 4: # pad NULLs
      round_arg += "\x00"

    round_value = 0  
    for i in range(len(round_arg)):
      achar = round_arg[i]
      if args.big_endian:
        round_value = (round_value << 8) | ord(achar) # Big Endian
      else:
        round_value = (ord(achar) << (i * 8)) | round_value # Little Endian
    print "String = {} Hex = 0x{:x}".format(round_value, round_value)
    rounds.append(round_value)

##########################################################################################
# Convert the string to use acceptable values during arithmetic ##########################
##########################################################################################

xs = []
ys = []
for desired_value in rounds:
  s = z3.Solver()
  x = z3.BitVec('x', 32)
  y = z3.BitVec('y', 32)

  if args.operation.lower() == "xor":
    s.append(x ^ y == desired_value)
  elif args.operation.lower() == "subtract":
    s.append(x - y == desired_value)
  else:
    s.append(x + y == desired_value)
    
  for i in range(0, 4):
    xchar = z3.Extract(((i + 1) * 8) - 1, i * 8, x)
    ychar = z3.Extract(((i + 1) * 8) - 1, i * 8, y)
    for j in BAD_CHARS:
      s.append(xchar != j)
      s.append(ychar != j)

  result = s.check()
  if result == z3.sat:
    model = s.model()
    xs.append(model.eval(x).as_long())
    ys.append(model.eval(y).as_long())
    combined = (xs[-1] + ys[-1]) & 0xffffffff
    print "x = 0x{:x} y = 0x{:x} combined = 0x{:x} ({})".format(xs[-1], ys[-1], combined, binascii.unhexlify("{:08x}".format(combined)))
  else:
    print result
    print s.to_smt2()

x_string = "x = ["
y_string = "y = ["
for i in range(len(xs)):
  if i != 0:
    x_string += ", "
    y_string += ", "
  x_string += "0x{:x}".format(xs[i])
  y_string += "0x{:x}".format(ys[i])

print "\n" + args.operation + " Values:\n" + x_string + "]\n" + y_string + "]"


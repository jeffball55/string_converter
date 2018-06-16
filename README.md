A small utility to encode a string such that it avoids bad bytes by using arithmetic. Useful for when creating ROP chains in
bugs that need to avoid bad bytes.  It uses Z3 to solve for a set of 2 values with no bad bytes that will add/subtract/xor to
your desired value.


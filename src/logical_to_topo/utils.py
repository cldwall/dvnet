# Taken from https://github.com/skorokithakis/shortuuid/blob/8c0acd41b02595641624d25e12ef4c6fbcca1c2e/shortuuid/main.py
def intToString(number, alphabet, padding  =None):
    """
    Convert a number to a string, using the given alphabet.
    The output has the most significant digit first.
    """
    output = ""
    alpha_len = len(alphabet)
    while number:
        number, digit = divmod(number, alpha_len)
        output += alphabet[digit]
    if padding:
        remainder = max(padding - len(output), 0)
        output = output + alphabet[0] * remainder
    return output[::-1]

'''The script used for generating impulses and processing impulse responses.

Modify the `main` function below to change between generating and processing modes.

Note that this file can also be imported as a module.
'''

import sys

import numpy as np
from scipy.io import wavfile

DTYPE = np.int16

NUM_IMPULSES = 32
SPACING = 1
SAMPLE_RATE = 48000


def gen_amplitudes(min_amplitude=-60, num_impulses=NUM_IMPULSES):
    amplitude_spacing = abs(min_amplitude) / (num_impulses // 2)
    amplitudes_db = np.linspace(
        min_amplitude, 0, num_impulses // 2, endpoint=False)
    amplitudes_db += amplitude_spacing / 2
    amplitudes_db = np.flip(amplitudes_db)
    amplitudes = 10 ** (amplitudes_db / 20)
    amplitudes = np.concatenate((amplitudes, -amplitudes))
    return amplitudes


def generate_impulses(filename, num_impulses=NUM_IMPULSES, spacing_secs=1, sample_rate=48000, dtype=np.int16):
    '''Generate impulses of decaying amplitude, writing the result to a WAV file.

    The first half of the impulses are positive; the second half are negative.
    '''

    # the length, with padding at the beginning and end equal to one impulse response length
    len_seconds = (num_impulses + 2) * spacing_secs
    len_samples = len_seconds * sample_rate

    amplitudes = gen_amplitudes(num_impulses=num_impulses)
    amplitudes *= dtype_max
    amplitudes = amplitudes.astype(dtype)

    dtype_max = np.iinfo(dtype).max
    data = np.zeros(len_samples, dtype=dtype)
    for i, amp in enumerate(amplitudes):
        n = (i + 1) * spacing_secs * sample_rate
        data[n] = amp

    wavfile.write(filename, sample_rate, data)


def process_irs(recorded_ir_filename, processed_ir_filename, num_impulses=NUM_IMPULSES, spacing_secs=SPACING, ir_len=128):
    '''Process impulse responses (recorded by playing back a file written by `generate_impulses`) into the format used by the amp sim plugin.'''

    sample_rate, recorded_irs = wavfile.read(recorded_ir_filename)
    dtype = recorded_irs.dtype
    dtype_max = np.iinfo(dtype).max
    recorded_irs = recorded_irs.astype(np.float64) / dtype_max

    # the length of each impulse response
    recorded_ir_len = round(spacing_secs * sample_rate)

    # the first and last "IRs" should be padding of length spacing_secs, so let's ignore them
    recorded_irs = recorded_irs[recorded_ir_len:-recorded_ir_len]

    recorded_irs_size = num_impulses * recorded_ir_len
    # now irs should be irs_size long
    # if not, we'll proceed but print a warning
    if recorded_irs.size != recorded_irs_size:
        print(
            f"recorded impulse response file wrong length: ignoring the {spacing_secs}-second padding on either side, it should be {recorded_irs_size} samples long, but is instead {recorded_irs.size} samples long", file=sys.stderr)
        recorded_irs = recorded_irs[:recorded_irs_size]

    # reshape it so each IR is one row of the matrix
    recorded_irs = np.reshape(recorded_irs, (num_impulses, recorded_ir_len))

    # now, truncate everything past ir_len samples
    recorded_irs = recorded_irs[:, :ir_len]

    # we need to rescale the IRs by the original amplitude
    amplitudes = gen_amplitudes(num_impulses=num_impulses)
    # converting 1d array to transposed 2d array
    amplitudes = amplitudes[np.newaxis].T

    recorded_irs /= amplitudes

    # now put recorded_irs back-to-back
    recorded_irs = recorded_irs.flatten()

    wavfile.write(processed_ir_filename, sample_rate, recorded_irs)


def main():
    # generate_impulses("impulses.wav")
    process_irs("recorded_ir_bedroom.wav", "bedroom.wav")


if __name__ == "__main__":
    main()

# SoX Spectrogram Generator Plugin for Nicotine+

A plugin for [Nicotine+](https://nicotine-plus.org/) that generates spectrograms using [SoX](https://github.com/chirlu/sox) after a file has finished downloading.

![Spectrogram](https://i.imgur.com/LlXHtCA.png)

## 📖 How to use

- Create a folder named `sox_spectrogram_generator` in `C:\Users\<user>\AppData\Roaming\nicotine\plugins\` and copy the contents of the `src` folder into this new folder.

- You need to have the [SoX binary](https://sourceforge.net/projects/sox/) on your system. You can add it to your system PATH or set a custom path to the SoX binary in the plugin settings.

- Windows users only: since the **MAD decoder library** is not bundled with SoX for patent reasons, you will need to add it manually. You can either compile it yourself from [the source](https://www.underbit.com/products/mad/), or copy a compiled version of `libmad.dll` in the same directory as SoX binary. You can find the file [on this repository](https://github.com/ewauq/sox_spectrogram_generator/lib) which is provided by [videohelp.com](https://www.videohelp.com/software?d=sox-14.4.0-libmad-libmp3lame.zip).

## ⚙️ Settings

#### Path to SoX binary

The SoX path to the executable.

Leave the value empty if SoX is already in your system PATH. If not, you can specify the full path including the executable file.

- Default value : _empty_ (taken from the PATH)

#### Audio channel

Audio channel to generate the spectrogram from.

If you want to generate an audio spectrogram from just one channel, change it to _Left_ or _Right_.

- Default value: _Left and right_

#### Spectrogram width and height

Width and height in pixels of an audio channel spectrogram.

This refers to the size of the spectrogram area, not the overall image dimensions. For example, if you select _Left and Right_ channels, the final image height will be _2 × height_ plus space for default text, borders, and margins.

- Width range: _64_ to _200000_
- Width default value: _800_
- Height range: _64_ to _512_
- Height default value: _257_

Note: to prevent a slow generation, the height must always be a power of two plus one. The value will be automatically adjusted to fit this requirement (e.g., 512 will be modified to 513).

#### Title

Title to display at the top of the generated image.

It can be the filename without the extension, the filename with the extension or the full path including the filename and the extension. Be careful not to include sensitive information when using the full path option.

- Default value: _no title_

#### Comment

Comment to display at the bottom left of the image.

Some text to replace "Created by SoX". Be aware that if the comment is wider than the final image, it won't be displayed. If you want no comment at all, you can add a blank space.

- Default value: _Created by SoX_

#### Starting position

Starting analysis position in seconds.

If you want to start the audio analysis further from the beginning, you can specify the position in seconds from where it has to start. If the given value is higher than the audio length, it will produce a useless image.

- Default value: _0_

#### Duration

Duration of the analysis in seconds.

If you just want an audio spectrogram of a 30 seconds audio clip, change the value to 30. The analysis will start at the starting position previously set (see above).

- Default value: _0_

#### Window function

The window parameter to use to generate the audio spectrogram.

Available options:

- Hann: "_for good all-round frequency-resolution and dynamic-range properties_"
- Hamming: "_for better frequency resolution but lower dynamic-range_"
- Bartlett
- Rectangular
- Kaiser "_for higher dynamic-range but poorer frequency-resolution_"
- Dolph

(descriptions taken from the [SoX manual](https://linux.die.net/man/1/sox))

- Default value: _Hann_

#### Monochrome

Generate a monochromatic spectrogram

Will generate a black and white audio spectrogram image.

- Default value: _off_

#### Raw image

Hide axes and labels.

Will generate a raw spectrogram image without any text, borders, margins, just the spectrogram areas.

- Default value: _off_

#### High color mode

Use the high-intensity color mode.

Will saturate colors which is less visually pleasing than the default colour palette, but it may make it easier to differentiate different levels.

- Default value: _off_

#### Light mode

Use a white background instead of the black one.

- Default value: _off_

### Brightness

Allows brightness adjustments of the audio spectrogram, if needed.

- Range: _20_ to _180_
- Default value: _120_

#### Contrast

Allows contrast adjustments of the audio spectrogram, if needed.

- Range: _-100_ to _100_
- Default value: _0_

#### Number of colors

Allows to change the number of colors to render the audio spectrogram. Low values give a poster-like effect and produce smaller PNG files.

- Range: _1_ to _249_
- Default value: _249_

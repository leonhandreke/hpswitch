# hpswitch

`hpswitch` is a Python module to allow interaction with HP Networking switches in a pythonic fashion. It uses [paramiko](http://www.lag.net/paramiko/) to interact with the switch using the SSH2 protocol. Its goal is to be a more or less direct interface to the switch, without any additional abstraction layers.

## Status

Currently, only a very small subset of the functionality of the switch CLI is implemented.

`hpswitch` *should* be compatible with the 3500, 3500yl, 5400zl, 6200yl, 6600 and 8200zl switch series. However, it has so far only been tested with a 5406zl switch. If you can confirm compatibility with other switch models, please let me know!

## Documentation

Comments in `hpswitch` use the [Markdown](http://daringfireball.net/projects/markdown/) markup language. Pretty-looking and readable HTML can be generated using [pycco](http://fitzgen.github.com/pycco/).

## License

`hpswitch` licensed under an MIT License. See the `LICENSE` file in the repository root for more information. Contributions in the form of github Pull Requests are more than welcome!


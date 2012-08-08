# hpswitch

`hpswitch` is a Python module to allow interaction with HP Networking switches in a pythonic fashion.

It uses [pySNMP](http://pysnmp.sourceforge.net/) to interact with the switch using the SNMPv2 protocol.

`hpswitch` also depends on the `ipaddress` module. The functionality of this module is outlined in [PEP 3144](http://www.python.org/dev/peps/pep-3144/). A reference implementation is [provided by Google](http://code.google.com/p/ipaddr-py). If you don't care and you just want to get up and running quickly, the file to `wget` is `http://hg.python.org/cpython/raw-file/tip/Lib/ipaddress.py`.

## Status

Currently, only a very small subset of the functionality of the SNMP API is implemented, mostly related to dealing with IP addressing, VLANs and interfaces.

`hpswitch` *should* be compatible with the 3500, 3500yl, 5400zl, 6200yl, 6600 and 8200zl switch series. However, it has so far only been tested with a 5406zl switch. If you can confirm compatibility with other switch models, please let me know!

## Documentation

Comments in `hpswitch` use the [Markdown](http://daringfireball.net/projects/markdown/) markup language. Pretty-looking and readable HTML can be generated using [pycco](http://fitzgen.github.com/pycco/).

## License

`hpswitch` is licensed under the MIT License. See the `LICENSE` file in the repository root for more information. Contributions in the form of github Pull Requests are more than welcome!


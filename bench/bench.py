from typing import Optional, List
import enum
import attr
import cattr
import cProfile


@attr.s(slots=True, frozen=True)
class Lorem:
    ipsum = attr.ib()
    dolor = attr.ib()
    sit = attr.ib()
    amet = attr.ib()
    consectetur = attr.ib()
    adipiscing = attr.ib()


@attr.s(slots=True, frozen=True)
class Fugiat:
    eiusmod = attr.ib()
    tempor = attr.ib()
    incididunt = attr.ib()
    labore = attr.ib()
    dolore = attr.ib()
    magna = attr.ib()
    aliqua = attr.ib()
    veniam = attr.ib()
    nostrud = attr.ib()
    exercitation = attr.ib()
    ullamco = attr.ib()
    laboris = attr.ib()
    commodo = attr.ib()
    consequat = attr.ib()
    aute = attr.ib()


@attr.s(slots=True, frozen=True)
class Invenire:
    irure = attr.ib()
    reprehenderit = attr.ib()
    voluptate = attr.ib()
    velit = attr.ib()
    esse = attr.ib()
    cillum = attr.ib()
    eepcillum = attr.ib()


@attr.s(slots=True, frozen=True)
class Tritani:
    nulla = attr.ib()
    name = attr.ib()
    value = attr.ib()
    pariatur = attr.ib()
    exceptuer = attr.ib()


@attr.s(slots=True, frozen=True)
class Laborum:
    type = attr.ib()
    urangulal = attr.ib()
    ipsumal = attr.ib()
    occaecat = attr.ib()
    cupidatat = attr.ib()
    proident = attr.ib()


class Aliquip(enum.IntEnum):
    Aliquip1 = 1
    Aliquip2 = 2
    Aliquip3 = 3
    Aliquip4 = 4
    Aliquip5 = 5


@attr.s(slots=True, frozen=True)
class Assentior:
    aliquip = attr.ib(type=Aliquip)
    culpa = attr.ib()
    fugiat = attr.ib(type=Optional[Fugiat])
    invenire = attr.ib(type=Optional[Invenire])
    deserunt = attr.ib()
    lorem = attr.ib(type=Optional[Lorem])
    mollit = attr.ib()
    laborums = attr.ib(type=Optional[List[Laborum]])
    tantas = attr.ib()
    nominati = attr.ib()
    fabulas = attr.ib()
    tritani = attr.ib(type=Optional[Tritani])


@attr.s(slots=True, frozen=True)
class Dignissim:
    assentior = attr.ib(type=Assentior)
    new_cupidatat = attr.ib()
    laoreet = attr.ib()
    rationibus = attr.ib()


obj = Dignissim(
    assentior=Assentior(
        aliquip=Aliquip.Aliquip1,
        culpa=6,
        fugiat=Fugiat(
            eiusmod="aaaaaaaaaaaaaaaa",
            tempor="bbbbbb",
            incididunt="CCCCCCCCCCCCCCCCCCC",
            labore="dddddddddd",
            dolore="eeeeeeeeee",
            magna="fffffffffff",
            aliqua="gggggggggggggg",
            veniam=None,
            nostrud=None,
            exercitation=None,
            ullamco=None,
            laboris=None,
            commodo=None,
            consequat=None,
            aute=None,
        ),
        invenire=Invenire(
            irure=53,
            reprehenderit=153,
            voluptate=242,
            velit=100,
            esse=5035,
            cillum=53,
            eepcillum=422,
        ),
        deserunt=True,
        lorem=Lorem(
            ipsum=b"",
            dolor=[
                b';\xcd\xe5\xbf\x98\xbc\xd7\x12\xadp\xd9"#g\xdc\x1b;\n\xbc\xbd\x81\x0c\xaay\xe5$\x08\x0e\x8ch',
                b"\x9f\xe7\xa2{\xc5(\x1bget\xf3\xb38\xf8\xe4v\x1c\xe3SL:\x04\xb6\xc7k\xef\xfeX\xa0\x18",
                b"\xfd\x00\x92\xa5\x9d\xae\x1d\xdc'\xd9\x9d\xb5#w_6{\xb4\xa1\xc0\xfb\xdb\x9b\xc4Ww@\xa4V\x85"
                b"\x91fe\xa4\xe0\xcd\xde\xdd\xa6%\x89\x15\xcbT\xc3g\x8bjZ\xfe\xacU\x0c\xc7H\xdc\xdaHk1"
                b"\x11<m\\|\x1d\xb6\x83\x8f*\xd8\xddL\xb1~$m$\x99-\x86Cj{!\x1f\xc1\x7f\xd5\xf2"
                b"\x0f\xb5x\xb6\x9f2\x1e\xc1\xcb\xbdD\xc8Z\x8892\xefp\xe08-#(2\x7f6>a\xbb&",
            ],
            sit=[
                b"\xc0/\x14\xd2\xfa\x1eGc\x84\xb4\x06\x91\x8c8\x0fS\xd1\xf0\xaa\x97RXd6\xee\xc2\x9d\xc4D/",
                b"\t\x0eM\xec\xce\x01%\xd6\rv\x95\x93d\xa9\x02\xac\xcc\x8f\xcav\x8a\x99\xc9\x15\x17\x93Q\xd7\x13\xb3",
                b"\xe57\xd9zm\xef8\xda\xe1h\x14\xf9-\x8f\xa9\xbc\x00\xc0\x07)i\xde\xc6;X!+{\xdb4",
                b"\x97\xbe(\x89\x9d\xc6\xb9\xf3Z\xfb\x0e\x02+f\xa4\x88\xc5\xfc\xba\xe6\x01\x9f\xb7\x87\xbc\xda\xaa\x83wC",
            ],
            amet=[
                b'L_;\x12\xf5\xf9\xcc\xae6\x9e\x98$s_\xd9\xca\x92\xfd\xdbs\x83\x04"\x86t+\xbb\xf69g',
                b" \xc7\xde\xff\xe3r**\x08?J\x0ba7\x9c\xf3\xaf\x99\xcc6\xe4\xbb\x9a\\\xb5q?ey\x9b",
                b"\x84\xe8'\xb7\xd6\xdcR\x135\x00\x96\xa3\xea\xffIc\x9a\xf2\xa7\t\xe2\xb4\x07\x9e\xf49-\"\x1d\xa3",
                b"J\n\xf7\xedcB]\r\xb2L\xaf\xbc\x9b\x92\xfe\xb4\x95L\xde\xf3\xe7r\xdf\x16\xbcID\x8f\x07\x91",
                b"PDf\x91\x01?)G\x8d\xe1T\r\x1b\x8aL=\xffe\xcc\xa1\xab\x9a\xf8\xdeN^\x06\xdf\xc2\x95",
                b"\x8e\x9e\\$\xed\xa2p\x12,=\x8c\x8d\x84J\xe6\xfc\xe1\x88y#\x9a'\xfc\x04\xba\x13\x10\xa3\xf5\xba",
                b"\xa9\xc6 \xf3\xee;\x94\xe7\xeb\xb28\x1d\x93\nt\xa5H\x06\xcc\xd3\xf3\x9e%\x93\x89\x9d\xe4]!E",
                b"\xef\xfa\x04\xa9 \x8cI\xa7*\x98\xc7+O\xba\x833^\x0fw\x95\x89Y\x932\x1f-\xaa#\x08U",
            ],
            consectetur=b"\x17\xfe\xf9\x1b\x8a\xc9\xbc\x95\xc4\xdc8\xcb\x9b{\x9eF\x8b\x89\xf8\x07`\x8eo\x11\xc9\x98\x07I\xd2\x1b",
            adipiscing=b"wy\xe9\xd9^\x7f<\x14\xae\x86\xf33Y\xcd/\xb4b\x85\x18\xd9~,\xb6@\xd3g\x17\xa4\xf0\xbc",
        ),
        mollit=4294967294,
        laborums=[
            Laborum(
                type=23,
                urangulal=b"\xd1c\xe0\x1dT\xf1\xde\x8f\xeb\x9d\xfd\xcf\x88\xe0\xcc\xda\x9er\xbdqJ/\xf0\x11\x97\\'&\xa6>",
                ipsumal=None,
                occaecat=b"\x13\xa9f{dr\x1a/\x15\xbc\xcb/7ax\xc9\x98\xb9\xd8s\xc8%\x9a\xf6wH\xf6\x0bg&",
                cupidatat=13,
                proident=None,
            ),
        ],
        tantas="sdfsdlxcv49249sdfs90sdf==",
        nominati=-1,
        fabulas=False,
        tritani=None,
    ),
    new_cupidatat=13,
    laoreet=1,
    rationibus=False,
)


converter = cattr.Converter()


def bench():
    unstructured = converter.unstructure_attrs_asdict(obj)
    converter.structure_attrs_fromdict(unstructured, obj.__class__)


cProfile.run("""for i in range(25000): bench()""", sort="tottime")

import marshmallow as mm

from pypedream.messages import Payload, PypedreamMessage


class OGPayload(Payload):
    og_id = mm.fields.Int()


def test_messages():
    og1 = OGPayload(epoch=0, type=OGPayload.dotted_path(), og_id=1)
    pl1 = Payload(epoch=0, type=Payload.dotted_path())
    pd1 = PypedreamMessage(
        id=0, type=PypedreamMessage.dotted_path(), metadata={}, payload=og1
    )
    pd2 = PypedreamMessage(
        id=0, type=PypedreamMessage.dotted_path(), metadata={}, payload=pl1
    )
    print(pd1.dumps())
    print(pd2.dumps())
    pd2 = pd2.with_payload(og1)
    print(pd2.dumps())

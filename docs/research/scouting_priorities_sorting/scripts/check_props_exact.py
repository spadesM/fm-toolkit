import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

dump_fast("StreamedTable.UxmlSerializedData.Deserialize (part 2)", 0x015f3a00, 0x015f4180)
dump_fast("PropertyRegistration (ScoutPlayerPriorities 0x00468000..0x00468700)", 0x00468000, 0x00468700)
dump_fast("PropertyRegistration (SpecificallyScoutedPerson 0x0046ad00..0x0046b500)", 0x0046ad00, 0x0046b500)
dump_fast("SpecificallyScoutedPersonReference methods (0x00697200..0x00697600)", 0x00697200, 0x00697600)

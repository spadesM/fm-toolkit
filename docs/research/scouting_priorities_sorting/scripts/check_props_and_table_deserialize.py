import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from dump_headers_fast import dump_fast

# 1. Dump StreamedTable.UxmlSerializedData.Deserialize (0x015f36b0)
dump_fast("StreamedTable.UxmlSerializedData.Deserialize", 0x015f36b0, 0x015f36b0 + 0x350)

# 2. Check PropertyRegistration around 0x00468300 and 0x0046b000, and SpecificallyScoutedPersonReference.GetPropertiesInternal (0x00696f80)
dump_fast("SpecificallyScoutedPersonReference.GetPropertiesInternal", 0x00696f80, 0x00696f80 + 0x350)
dump_fast("ScoutPlayerPrioritiesReference.GetPropertiesInternal", 0x0067d360, 0x0067d360 + 0x450)
dump_fast("PropertyRegistration.Initialise (ScoutPlayerPriorities @ 0x00468300)", 0x00468300, 0x00468300 + 0x280)
dump_fast("PropertyRegistration.Initialise (SpecificallyScoutedPerson @ 0x0046b000)", 0x0046b000, 0x0046b000 + 0x300)

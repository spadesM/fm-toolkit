import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\mcaka\.gemini\antigravity\brain\f3fe4be7-d8a5-4ec7-895a-ec06f09f2529\scratch")
import dump_headers_fast as dhf

# Let's check what metadata tables exist in global-metadata.dat
hdr = struct.unpack_from("<64I", dhf.meta, 0)
# Il2CppGlobalMetadataHeader offsets:
# 0: sanity, 1: version
# 2,3: stringLiteralOffset, stringLiteralSize
# 4,5: stringLiteralDataOffset, stringLiteralDataSize
# 6,7: stringOffset, stringSize
# 8,9: eventsOffset, eventsSize
# 10,11: propertiesOffset, propertiesSize
# 12,13: methodsOffset, methodsSize
# 14,15: parameterDefaultValuesOffset
# 16,17: fieldDefaultValuesOffset
# 18,19: fieldAndParameterDefaultValueDataOffset
# 20,21: fieldMarshaledSizesOffset
# 22,23: parametersOffset
# 24,25: fieldsOffset, fieldsSize
# 26,27: genericParametersOffset
# 28,29: genericParameterConstraintsOffset
# 30,31: genericContainersOffset
# 32,33: nestedTypesOffset
# 34,35: interfacesOffset
# 36,37: vtableMethodsOffset
# 38,39: interfaceOffsetsOffset
# 40,41: typeDefinitionsOffset, typeDefinitionsSize

# Also dump full bytes of Bindings.GetNthProperty (0x014c1450..0x014c1650) and SortComparer.Compare (0x015a3d30..0x015a4040)
dhf.dump_fast("Bindings.GetNthProperty_FULL", 0x014c1450, 0x014c1660)
dhf.dump_fast("SortComparer.Compare_FULL", 0x015a3d30, 0x015a4040)
dhf.dump_fast("StreamedTable.CanSortColumn_or_sub_15e58c0", 0x015e58c0, 0x015e5a50)

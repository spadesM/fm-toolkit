import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Repos\fm26save")
import UnityPy
from fm26save.binary_decompiler import resolve_fm_install_dir

root = resolve_fm_install_dir()
bundle_dir = root / "fm_Data/StreamingAssets/aa/StandaloneWindows64"

def inspect_bundle_tables(bundle_name):
    print(f"\n==================== {bundle_name} ====================")
    env = UnityPy.load(str(bundle_dir / bundle_name))
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            tt = obj.read_typetree()
        except Exception:
            continue
        name = tt.get("m_Name", "")
        ve_assets = tt.get("m_VisualElementAssets", [])
        if not ve_assets:
            continue
        tables = [v for v in ve_assets if "StreamedTable" in v.get("m_FullTypeName", "")]
        if not tables:
            continue
        print(f"\n--- Asset: {name} (PathID={obj.path_id}) ---")
        # Find serialized data for each StreamedTable
        refs = tt.get("references", {}).get("root", {}).get("objects", {})
        # Note: UnityPy typetree for ManagedReferencesRegistry
        ref_list = tt.get("references", {}).get("RefIds", [])
        ref_map = {}
        for r in ref_list:
            rid = r.get("rid")
            ref_map[rid] = r.get("data", {})
        for t in tables:
            sd_rid = t.get("m_SerializedData", {}).get("rid")
            data = ref_map.get(sd_rid, {})
            print(f"  Table id={t.get('m_Id')} fullType={t.get('m_FullTypeName')} classes={t.get('m_Classes')}:")
            for k, v in data.items():
                if k in ("m_binding", "m_sortBinding", "m_sortAscending", "m_disableSorting", "m_defaultSortColumn",
                         "m_dragCellId", "m_removeCellId", "m_selectionCellId", "m_reorderable", "m_dragEvents",
                         "m_tableConfig", "m_tableViews", "m_tableViewCollection", "m_viewDropdownName",
                         "m_allowColumnReordering", "m_allowColumnResizing", "m_selectionMode"):
                    print(f"    {k}: {v}")

inspect_bundle_tables("ui-recruitment_assets_all.bundle")

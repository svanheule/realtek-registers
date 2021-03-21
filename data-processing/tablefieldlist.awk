# #if defined(CONFIG_SDK_CHIP_FEATURE_ADDRESS_TABLE_LOOKUP)
# #if defined(CONFIG_SDK_RTL8390)
# rtk_tableField_t RTL8390_L2_CAM_IP_MC_FIELDS[] =
# {
#     {   /* name     CYPRESS_L2_CAM_IP_MC_FID_RVIDtf */
#         /* lsp */   84,
#         /* len */   12,
#     },
#     {   /* name     CYPRESS_L2_CAM_IP_MC_ZEROtf */
#         /* lsp */   64,
#         /* len */   20,
#     },
#     {   /* name     CYPRESS_L2_CAM_IP_MC_GIPtf */
#         /* lsp */   32,
#         /* len */   32,
#     },
#     {   /* name     CYPRESS_L2_CAM_IP_MC_IP_MCtf */
#         /* lsp */   31,
#         /* len */   1,
#     },
#     {   /* name     CYPRESS_L2_CAM_IP_MC_IP6_MCtf */
#         /* lsp */   30,
#         /* len */   1,
#     },
#     {   /* name     CYPRESS_L2_CAM_IP_MC_MC_PMSK_IDXtf */
#         /* lsp */   6,
#         /* len */   12,
#     },
# };


/^#if defined\(CONFIG_SDK_CHIP_FEATURE/ {
    feature_name = gensub(/^.+FEATURE_([0-9A-Z_]+)\)$/, "\\1", "g");
    feature_name = gensub(/[_]+/, "_", "g", feature_name)
}

/rtk_tableField_t/ {
    table_name = gensub(/^[^ ]+ ([0-9A-Z_]+)_FIELDS\[\] =$/, "\\1", "g");
}

/\/\* name /{
    field_name = gensub(/^.+[[:space:]]+([0-9A-Z_]+)tf \*\/$/, "\\1", "g");
}

/\/\* lsp \*\//{
    field_lsb = gensub(/^.+[[:space:]]+([0-9A-F]+),$/, "\\1", "g");
}

/\/\* len \*\//{
    field_len = gensub(/^.+[[:space:]]+([0-9A-F]+),$/, "\\1", "g");
    print feature_name "," table_name "," field_name "," field_lsb "," field_len
}

# #if defined(CONFIG_SDK_CHIP_FEATURE_INTERFACE)
# #if defined(CONFIG_SDK_RTL8380)
# rtk_regField_t GMII_INTF_SEL_RTL8380_FIELDS[] =
# {
#     {   /* name */          MAPLE_RESERVEDf,
#         /* lsp */           5,
#         /* len */           27,
#     },
#     {   /* name */          MAPLE_UART1_SELf,
#         /* lsp */           4,
#         /* len */           1,
#     },
#     {   /* name */          MAPLE_JTAG_SELf,
#         /* lsp */           2,
#         /* len */           2,
#     },
#     {   /* name */          MAPLE_GMII_IF_SELf,
#         /* lsp */           0,
#         /* len */           2,
#     },
# };
# #endif


/^#if defined\(CONFIG_SDK_CHIP_FEATURE/ {
    feature_name = gensub(/^.+FEATURE_([0-9A-Z_]+)\)$/, "\\1", "g");
    feature_name = gensub(/[_]+/, "_", "g", feature_name)
}

/rtk_regField_t/ {
    reg_name = gensub(/^[^ ]+ ([0-9A-Z_]+)_FIELDS\[\] =$/, "\\1", "g");
}

/\/\* name \*\//{
    field_name = gensub(/^.+[[:space:]]+([0-9A-Z_]+)f,$/, "\\1", "g");
}

/\/\* lsp \*\//{
    field_lsb = gensub(/^.+[[:space:]]+([0-9A-F]+),$/, "\\1", "g");
}

/\/\* len \*\//{
    field_len = gensub(/^.+[[:space:]]+([0-9A-F]+),$/, "\\1", "g");
    print feature_name "," reg_name "," field_name "," field_lsb "," field_len
}

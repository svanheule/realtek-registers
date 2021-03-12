# if defined(CONFIG_SDK_CHIP_FEATURE_CHIP_INFORMATION)
# #if defined(CONFIG_SDK_RTL9310)
#    {   /* register name        INT_MANGO_CHIP_INFO_DMY_RTL9310 */
#        /* offset address */    0x0,
#        /* field numbers */     1,
#        /* port index */        0, 0,
#        /* array index */       0, 0,
#        /* portlist index */    0,
#        /* bit offset */        0,
#        /* register fields */   CHIP_INFO_DMY_RTL9310_FIELDS,
#    },

/^#if defined\(CONFIG_SDK_CHIP_FEATURE/ {
    feature_name = gensub(/^.+FEATURE_([0-9A-Z_]+)\)$/, "\\1", "g");
    feature_name = gensub(/[_]+/, "_", "g", feature_name)
}

/register name/ {
    register_name = gensub(/^.+register name[[:space:]]+([0-9A-Z_]+) \*\/$/, "\\1", "g");
}

/offset address/ {
    offset_hex = gensub(/^.+[[:space:]]+0x([0-9A-F]+),$/, "\\1", "g");
}

/field numbers/ {
     field_numbers = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/port index/ {
    port_index_lo = gensub(/^.+[[:space:]]+([0-9]+),[[:space:]]+([0-9]+),$/, "\\1", "g");
    port_index_hi =  gensub(/^.+[[:space:]]+([0-9]+),[[:space:]]+([0-9]+),$/, "\\2", "g");
}

/array index/ {
    array_index_lo =  gensub(/^.+[[:space:]]+([0-9]+),[[:space:]]+([0-9]+),$/, "\\1", "g");
    array_index_hi =  gensub(/^.+[[:space:]]+([0-9]+),[[:space:]]+([0-9]+),$/, "\\2", "g");
}

/portlist index/ {
    portlist_index = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/bit offset/ {
    bit_offset = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/register fields/ {
    print feature_name "," register_name "," offset_hex "," field_numbers \
        "," port_index_lo "," port_index_hi \
        "," array_index_lo "," array_index_hi \
        "," portlist_index "," bit_offset;
}

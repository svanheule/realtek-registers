#if defined(CONFIG_SDK_CHIP_FEATURE_ADDRESS_TABLE_LOOKUP)
#if defined(CONFIG_SDK_RTL8390)
#    {   /* table name               INT_CYPRESS_RTL8390_L2_CAM_IP_MC */
#        /* access table set */      99,
#        /* access table type */     1,
#        /* table size */            64,
#        /* total data registers */  3,
#        /* total field numbers */   CYPRESS_L2_CAM_IP_MCFIELD_LIST_END,
#        /* table fields */          RTL8390_L2_CAM_IP_MC_FIELDS
#    },
#endif

/^#if defined\(CONFIG_SDK_CHIP_FEATURE/ {
    feature_name = gensub(/^.+FEATURE_([0-9A-Z_]+)\)$/, "\\1", "g");
    feature_name = gensub(/[_]+/, "_", "g", feature_name)
}

/table name/ {
    table_name = gensub(/^.+table name[[:space:]]+([0-9A-Z_]+) \*\/$/, "\\1", "g");
}

/access table set/ {
    access_set = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/access table type/ {
    access_type = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/table size/ {
    table_size = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/total data registers/ {
    data_registers = gensub(/^.+[[:space:]]+([0-9]+),$/, "\\1", "g");
}

/table fields/ {
    print feature_name "," table_name "," \
        access_set "," access_type "," \
        table_size "," data_registers;
}

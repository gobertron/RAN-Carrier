namespace RAN.Australis {
// The fixed native asset layout must bind before this controller admits work.
// These are readiness names only: no position, visibility or animation write
// is performed on any fixed gun, pedestal, platform or support.
internal static class FixedCiwsData {
    public static readonly string[] RequiredNames={
        "CIWS_Mount_1","CIWS_Gun_1","FixedCIWS_1_PermanentPlatform",
        "CIWS_Mount_2","CIWS_Gun_2","FixedCIWS_2_PermanentPlatform",
        "CIWS_Mount_3","CIWS_Gun_3","FixedCIWS_3_PermanentPlatform",
        "CIWS_Mount_4","CIWS_Gun_4","FixedCIWS_4_PermanentPlatform",
        "CIWS_Mount_5","CIWS_Gun_5","FixedCIWS_5_PermanentPlatform"
    };
}
}

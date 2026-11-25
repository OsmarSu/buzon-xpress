import type { ConfigContext, ExpoConfig } from "expo/config";

export default function configure({ config }: ConfigContext): Partial<ExpoConfig> {
  if (process.env.BUZON_ANDROID_ARM64 !== "1") return config;

  return {
    ...config,
    plugins: [
      ...(config.plugins ?? []),
      ["expo-build-properties", { android: { buildArchs: ["arm64-v8a"] } }],
    ],
  };
}

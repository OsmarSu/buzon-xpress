import { useEffect, useState } from "react";
import { Animated, Image, Platform, StyleSheet } from "react-native";
import * as SplashScreen from "expo-splash-screen";
import { useReducedMotion } from "react-native-reanimated";

void SplashScreen.preventAutoHideAsync().catch(() => {});

export function StartupSplash() {
  const [imageReady, setImageReady] = useState(false);
  const [visible, setVisible] = useState(true);
  const [opacity] = useState(() => new Animated.Value(1));
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!imageReady) return;

    SplashScreen.hide();
    const timer = setTimeout(() => {
      if (reduceMotion) {
        setVisible(false);
        return;
      }
      Animated.timing(opacity, {
        toValue: 0,
        duration: 300,
        useNativeDriver: Platform.OS !== "web",
        isInteraction: false,
      }).start(({ finished }) => {
        if (finished) setVisible(false);
      });
    }, 1000);

    return () => {
      clearTimeout(timer);
      opacity.stopAnimation();
    };
  }, [imageReady, opacity, reduceMotion]);

  if (!visible) return null;

  return <Animated.View
    style={[styles.overlay, { opacity }]}
    importantForAccessibility="no-hide-descendants"
    accessibilityElementsHidden
  >
    <Image
      source={require("../../assets/logo-mision.png")}
      style={styles.logo}
      resizeMode="contain"
      onLoadEnd={() => setImageReady(true)}
    />
  </Animated.View>;
}

const styles = StyleSheet.create({
  overlay: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ffffff",
  },
  logo: { width: 180, height: 180 },
});

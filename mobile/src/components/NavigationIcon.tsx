import Svg, { Circle, Path } from "react-native-svg";
import { c } from "./theme";

export type NavigationIconName = "tracking" | "custodies" | "points" | "notices" | "account";
export function NavigationIcon({ name, color = c.navy, size = 24 }: { name: NavigationIconName; color?: string; size?: number }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" accessible={false} pointerEvents="none">
    {name === "tracking" && <><Circle cx={10.5} cy={10.5} r={6.5} /><Path d="m15.5 15.5 5 5" /></>}
    {name === "custodies" && <Path d="M12 3 3 7.5v9L12 21l9-4.5v-9ZM3 7.5l9 4.5 9-4.5M12 12v9M7.5 5.25l9 4.5" />}
    {name === "points" && <><Path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" /><Circle cx={12} cy={10} r={2.7} /></>}
    {name === "notices" && <Path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />}
    {name === "account" && <><Circle cx={12} cy={7.5} r={3.5} /><Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" /></>}
  </Svg>;
}

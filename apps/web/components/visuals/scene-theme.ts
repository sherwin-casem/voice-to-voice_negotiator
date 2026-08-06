import * as THREE from "three";

export const TEAL = new THREE.Color("#14b8a6");
export const CYAN = new THREE.Color("#22d3ee");
export const DEEP_BG = "#0a1628";

export function lerpAccent(mix: number) {
  return TEAL.clone().lerp(CYAN, mix);
}

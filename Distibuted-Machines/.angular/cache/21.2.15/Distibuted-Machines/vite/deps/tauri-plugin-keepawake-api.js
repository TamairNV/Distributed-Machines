import {
  invoke
} from "./chunk-3Q3OAZPQ.js";
import "./chunk-GOMI4DH3.js";

// node_modules/tauri-plugin-keepawake-api/dist-js/index.js
async function start(config) {
  return await invoke("plugin:keepawake|start", { config });
}
async function stop() {
  return await invoke("plugin:keepawake|stop");
}
export {
  start,
  stop
};
//# sourceMappingURL=tauri-plugin-keepawake-api.js.map

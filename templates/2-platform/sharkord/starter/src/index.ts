import { PluginConfig, PluginContext } from "@sharkord/plugin-sdk";

export default function plugin(context: PluginContext): PluginConfig {
  context.log(`🔌 {{PROJECT_NAME}} loaded`);

  // Register commands
  // context.commands.register({ ... });

  // Subscribe to events
  // context.events.on("voice", (event) => { ... });

  return {
    name: "{{PROJECT_NAME}}",
    version: "{{INITIAL_VERSION}}",
    onLoad() {
      context.log("Plugin loaded");
    },
    onUnload() {
      context.log("Plugin unloaded");
    },
  };
}

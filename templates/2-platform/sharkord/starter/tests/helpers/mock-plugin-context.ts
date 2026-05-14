import { PluginContext } from "@sharkord/plugin-sdk";

/**
 * Mock PluginContext for unit and integration tests.
 * Provides stubbed implementations of all PluginContext methods.
 */
export function createMockPluginContext(): PluginContext {
  return {
    log: (msg: string) => console.log(`[MOCK] ${msg}`),
    debug: (msg: string) => console.debug(`[MOCK] ${msg}`),
    error: (msg: string) => console.error(`[MOCK] ${msg}`),
    path: "/mock/plugin/path",
    events: {
      on: () => {},
      off: () => {},
      emit: () => {},
    },
    commands: {
      register: () => {},
    },
    settings: {
      register: () => {},
      get: () => null,
    },
    voice: {
      getRouter: () => null,
      createStream: () => null,
      getListenInfo: () => ({ ip: "127.0.0.1", announcedAddress: "127.0.0.1" }),
    },
  } as unknown as PluginContext;
}

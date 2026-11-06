/* eslint-disable @typescript-eslint/no-explicit-any */
import testConfig from './config.json'

// `testPortType` (from the TEST_PORT_TYPE env var, e.g. "pty" or "com0com") also applies the
// `${envName}-${testPortType}` section of config.json, for virtual ports that can do less, or more,
// than the hardware the platform section was written for
export const makeTestFeature = (envName: string, testPort?: string, testPortType?: string) => {
  const config = {
    ...testConfig.all,
    ...(testConfig as any)[envName],
    ...(testPortType ? (testConfig as any)[`${envName}-${testPortType}`] : {}),
  }

  const testFeature = (feature: string, description: string, callback: () => any) => {
    if (config[feature] === false) {
      return it(`Feature "${feature}" is disabled in "${envName}. "${description}"`)
    }
    it(description, callback)
  }

  const testHardware = (description: string, callback: () => any) => {
    if (!testPort) {
      return it(`${description} - Cannot be tested. Set the TEST_PORT env var with an available serialport for more testing.`)
    }
    it(description, callback)
  }

  const testHardwareFeature = (feature: string, description: string, callback: () => any) => {
    if (!testPort) {
      return it(`${description} - Cannot be tested. Set the TEST_PORT env var with an available serialport for more testing.`)
    }
    if (config[feature] === false) {
      return it(`Feature "${feature}" is disabled in "${envName}. "${description}"`)
    }
    it(description, callback)
  }

  const describeHardware = (description: string, callback: () => any) => {
    if (!testPort) {
      return it(`${description} - Cannot be tested. Set the TEST_PORT env var with an available serialport for more testing.`)
    }
    describe(description, callback)
  }

  return {
    testFeature,
    testHardwareFeature,
    testHardware,
    describeHardware,
  }
}

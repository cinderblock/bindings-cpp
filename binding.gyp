{
  'variables': {
    'openssl_fips': '',
    # Instrument the native code for coverage reports: `npm run rebuild -- --debug --coverage`
    # Linux and macOS write gcov data. Windows needs no compiler flags, because OpenCppCoverage
    # reads the debug build's PDB. See CONTRIBUTING.md.
    'coverage%': 'false'
  },
  'targets': [{
    'target_name': 'bindings',
    'sources': [
      'src/serialport.cpp'
    ],
    'include_dirs': ["<!(node -p \"require('node-addon-api').include_dir\")"],
    'cflags!': [ '-fno-exceptions' ],
    'cflags_cc!': [ '-fno-exceptions' ],
    "defines": ["NAPI_CPP_EXCEPTIONS"],
    'conditions': [
      ['OS=="win"',
        {
          'defines': ['CHECK_NODE_MODULE_VERSION'],
          'sources': [
            'src/serialport_win.cpp'
          ],
          'msvs_settings': {
            'VCCLCompilerTool': {
              'ExceptionHandling': '1',
              'DisableSpecificWarnings': [ '4530', '4506' ],
            }
          }
        }
      ],
      ['OS=="mac"',
        {
          'sources': [
            'src/serialport_unix.cpp',
            'src/poller.cpp',
            'src/darwin_list.cpp'
          ],
          'xcode_settings': {
            'GCC_ENABLE_CPP_EXCEPTIONS': 'YES',
            'MACOSX_DEPLOYMENT_TARGET': '10.9',
            'OTHER_CFLAGS': [
              '-arch x86_64',
              '-arch arm64'
            ],
            'OTHER_LDFLAGS': [
              '-framework CoreFoundation',
              '-framework IOKit',
              '-arch x86_64',
              '-arch arm64'
            ]
          }
        }
      ],
      ['OS=="linux"',
        {
          'sources': [
            'src/serialport_unix.cpp',
            'src/poller.cpp',
            'src/serialport_linux.cpp'
          ]
        }
      ],
      ['OS=="android"',
        {
          'sources': [
            'src/serialport_unix.cpp',
            'src/poller.cpp',
            'src/serialport_linux.cpp'
          ]
        }
      ],
      ['OS!="win"',
        {
          'sources': [
            'src/serialport_unix.cpp',
            'src/poller.cpp'
          ]
        }
      ],
      ['coverage=="true" and OS!="win"',
        {
          # The compiler driver links the matching runtime (libgcov, or clang's profile runtime)
          'cflags': [ '--coverage' ],
          'ldflags': [ '--coverage' ],
          'xcode_settings': {
            'OTHER_CFLAGS': [ '--coverage' ],
            'OTHER_LDFLAGS': [ '--coverage' ],
            # Build only the host architecture: a universal build compiles each source twice,
            # and the second pass overwrites the first pass's .gcno notes file
            'OTHER_CFLAGS!': [ '-arch x86_64', '-arch arm64' ],
            'OTHER_LDFLAGS!': [ '-arch x86_64', '-arch arm64' ]
          }
        }
      ]
    ]
  }],
}

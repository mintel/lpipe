# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]


## [3.0.0] - 2020-06-09
- Reduced code complexity
- Add type hints
- Increase test coverage
- Bugfix: lpipe.sqs.delete_message_batch called boto3 incorrectly
- Breaking: sentry-sdk no longer a required dependency, install with `lpipe = {"extras": ["sentry"], "version": "*"}`, and enable it by setting `process_event(exception_handler=lpipe.contrib.sentry.capture)`
- Breaking: moved `lpipe.sentry` to `lpipe.contrib.sentry`
- Breaking: moved `lpipe._boto3` to `lpipe.contrib.boto3`
- Breaking: removed `lpipe.testing`, use the boto3-fixtures library instead
- Breaking: removed `lpipe.taxonomy`
- Breaking: renamed LpipeBaseException to LPBaseException (although, you shouldn't use the base class anyways)
- Breaking: renamed ServerlessLogger to LPLogger
- Breaking: renamed `lpipe.utils._repr` to `repr`
- Semi-Breaking: moved Action, Payload, and Queue classes into their own modules, but they're still imported into the top level module (i.e. `lpipe.Action` still works)
- Deprecated: moved `lpipe.utils` get_nested, set_nested to `lpipe.contrib.mindictive`, stubs still in place

## [2.0.15] - 2020-05-05
- To prevent log explosion, stop adding message kwargs by default to logger passed into user's functions.

## [2.0.14] - 2020-05-01
- Set lpipe.testing.awslambda default lambda name to "my_lambda"
- Fix formatting and linting errors

## [2.0.13] - 2020-03-13
- SQS: If any records fail, delete successful records from the queue before raising an exception.
- Fix bug in `lpipe._boto.proxy` where logger was undefined.

## [2.0.12] - 2020-03-11
- If `AWS_ENDPOINTS` is set with a string as dict (`"key=value,key=value"`) of service names and endpoints, create boto3 clients and resources with the appropriate `endpoint_url` for a service, if provided.

## [2.0.11] - 2020-03-10
- Add setup/teardown context managers for all AWS testing utils.

## [2.0.10] - 2020-03-10
- Update get_queue_arn() to request QueueArn specifically.

## [2.0.9] - 2020-03-10
- Update SQS testing create utils to create DLQs and redrive policies automatically.

## [2.0.8] - 2020-03-10
- Fix reference to event_source_arn in get_event_source()

## [2.0.7] - 2020-03-10
- Fix bug in `utils.get_enum_path()` when re-raising an error after catching a KeyError.

## [2.0.6] - 2020-03-10
- Print exception class dynamically when catching TypeError.

## [2.0.5] - 2020-03-10
- Pass entire payload via event rather than just the event_source_arn.

## [2.0.4] - 2020-03-10
- `utils.get_nested()` now has the option of setting a default value, and it will raise a KeyError if the requested keys don't exist.
- Unhandled exceptions will now be raised if debug is true.
- Move event and context into a single dict pased to functions as kwarg `event`.
- Pass event source ARN to Payload and, subsequently, to the event dict passed into functions.

## [2.0.3] - 2020-03-10
- Add ability to pass kwargs even if they aren't in the signature

## [2.0.2] - 2020-03-10
- Refactor most tests to just use moto.
- Add s3 testing helpers

## [2.0.1] - 2020-03-05
- Backfill CHANGELOG
- Pass event and context to every function

## [2.0.0] - 2020-03-05
- `context` is now a required argument of `process_event()`
- Allow `process_event()` without a `path_enum`/`Enum`. One will be automatically generated based on the `paths` provided.
- Refactor and document exception flow control. All lpipe errors will now inherit from `LpipeBaseException`.
- Move setup and tear-down testing utilities out of `conftest.py` and into `lpipe.testing` so they can be used consistently by all projects implementing lpipe.
- Add example of using moto to mock boto3.

## [1.4.0] - 2020-03-05
- Allow user to set `default_path`. Doing so will ignore all message structure and pass the entire message to the called function.

## [1.3.5] - 2020-01-06
- Add check_status to utils

## [1.3.4] - 2019-12-05
- `utils.get_nested` will attempt a getattr() call if HEAD isn't a dict.

## [1.3.3] - 2019-12-05
- Add `utils.set_nested` dict helper.

## [1.3.2] - 2019-10-09
- Add JSON encoder `utils.AutoEncoder` which handles encoding Enums.

## [1.3.1] - 2019-10-08
- Fix bug in ServerlessLogger where we were modifying the base class and emit test logs with context

## [1.3.0] - 2019-10-07
- Add ability to trigger pipeline directly with a QueueType.RAW which may be a dict or json string

## [1.2.0] - 2019-10-07
- Add ability to manually return a value for each action triggered by a message.
- Add optional context to sentry.init

## [1.1.2] - 2019-10-02
- Better dummy lambda venv install command pulled from the build harness

## [1.1.1] - 2019-09-24
- Capture unhandled errors with Sentry, if it is initialized.

## [1.1.0] - 2019-09-24
- Enable validation of function signatures where the default is None.

## [1.0.5] - 2019-09-23
- Pop logger:None off of action_kwargs before continuing so we don't get crazy kwargs during debug/testing.

## [1.0.4] - 2019-09-23
- Increase verbosity of InvalidInputError messages.
- Remove black from the env; it should be installed locally atm.

## [1.0.3] - 2019-09-11
- Fix date in CHANGELOG

## [1.0.2] - 2019-09-11
### Changed
- Switched function call back to nested dictionary expansion to fix "f() got multiple values for keyword argument 'logger'"
- Add kinesis build() tests matching those added for sqs in 1.0.1

## [1.0.1] - 2019-09-11
### Changed
- Updated lpipe.sqs.build to accept message_group_id
- Updated the function signatures of kinesis and sqs helpers for single and batch messages/records.

## [0.2.2] - 2019-09-6
### Added
- Assert Action() functions are instance of types.FunctionType

## [0.2.0] - 2019-09-5
### Added
- Validate event kwargs against function signatures, making required_params optional if a function is provided.
- Validate function signature type hints and defaults.

### Changed
- required_params only required if no functions are provided
- Only functions or paths are required by Action() constructor (no more blank constructor arguments)

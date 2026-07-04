# @workflow/serde

Serialization symbols for custom class serialization in Workflow SDK.

## Usage

<!-- @skip-typecheck - self-referential import -->

```ts
import { WORKFLOW_SERIALIZE, WORKFLOW_DESERIALIZE } from '@workflow/serde';

class MyClass {
  constructor(public value: string) {}

  static [WORKFLOW_SERIALIZE](instance: MyClass) {
    return { value: instance.value };
  }

  static [WORKFLOW_DESERIALIZE](data: { value: string }) {
    return new MyClass(data.value);
  }
}
```

## License

Apache-2.0

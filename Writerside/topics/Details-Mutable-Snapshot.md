# Details: Mutable Snapshot 만들기

## 변경 가능한 snapshot 이란? {#what-is-mutable-snapshot}

변경 가능한 snapshot 은 `Snapshot.takeMutableSnapshot()` API로 만들어집니다. 이 API는 격리된 상태 공간을 만들어, 그 안에서 상태 값을 안전하게 변경할 수 있도록 해 줍니다. 변경 사항은 snapshot 안에 머무르며, `apply()` 함수가 명시적으로 호출되기 전까지 전역 상태에 영향을 주지 않습니다. 테스트나 실험, 일시적인 상태 변경에 특히 유용한 메커니즘입니다.

mutable snapshot 은 애플리케이션 상태의 격리된 사본이며, 다음과 같은 일을 가능하게 합니다.

- 전역 상태를 건드리지 않고 로컬에서만 상태를 수정하기.
- 변경 사항을 commit 하기 전에 안전하게 테스트하거나 검증하기.
- 필요 없으면 변경을 그대로 폐기하기.

`apply()` 가 호출되면 snapshot 의 변경 사항이 전역 상태로 전파됩니다. 여러 snapshot 이 동일한 상태를 수정한 경우, 시스템은 미리 정의된(또는 사용자 정의) 충돌 해결 정책에 따라 충돌을 처리합니다.

### 예시: mutable snapshot 만들고 사용하기 {#example}

```kotlin
class User {
    var name: MutableState<String> = mutableStateOf("")
}

fun main() {
    val user = User()
    user.name.value = "skydoves"
    println("Initial name: ${user.name.value}") // 출력: skydoves

    // mutable snapshot 을 만듭니다.
    val mutableSnapshot = Snapshot.takeMutableSnapshot()

    // snapshot 안에서 상태를 변경합니다.
    mutableSnapshot.enter {
        user.name.value = "Android"
        println("Inside snapshot: ${user.name.value}") // 출력: Android
    }

    // 아직 전역 상태에는 반영되지 않았습니다.
    println("After snapshot but before apply: ${user.name.value}") // 출력: skydoves

    // snapshot 의 변경을 전역 상태로 propagate 합니다.
    mutableSnapshot.apply()
    println("After applying snapshot: ${user.name.value}") // 출력: Android

    // 자원 해제
    mutableSnapshot.dispose()
}
```
{title="MutableSnapshotExample.kt"}

### 예시 흐름 {#steps}

1. **초기 상태**: `User` 객체가 만들어지고 초기 이름은 `"skydoves"` 입니다.
2. **snapshot 생성**: `Snapshot.takeMutableSnapshot()` 으로 mutable snapshot 을 만듭니다.
3. **snapshot 내부에서 상태 변경**: `enter` 블록 안에서 `name` 을 `"Android"` 로 갱신합니다. 이 변경은 snapshot 에 한정되며 전역 상태에는 영향이 없습니다.
4. **apply 이전 상태 확인**: `enter` 블록을 빠져나오면 전역 상태는 여전히 `"skydoves"` 입니다.
5. **snapshot 적용**: `apply()` 가 호출되면 snapshot 의 변경이 전역 상태로 전파됩니다.

### 핵심 포인트 {#key-points}

- **격리(Isolation)**: snapshot 안의 변경은 apply 되기 전까지 격리됩니다.
- **명시적 적용(Explicit Application)**: 전역 상태에 변경을 commit 하려면 반드시 `apply()` 를 호출해야 합니다.
- **안전성(Safety)**: snapshot 을 적용하지 않기로 결정하면, dispose 시점에 변경 사항이 그대로 폐기됩니다.

### Mutable Snapshot 의 장점 {#advantages}

1. **상태 실험(State Experimentation)**: 라이브 상태에 영향을 주지 않으면서 안전하게 상태 변경을 시험해 볼 수 있습니다.
2. **되돌릴 수 있음(Revertibility)**: snapshot 을 적용하지 않는 것만으로 변경을 폐기할 수 있습니다.
3. **충돌 해결(Conflict Resolution)**: 여러 snapshot 이 같은 상태를 수정한 경우 사용자 정의 정책으로 충돌을 처리할 수 있습니다.

### 언제 사용하면 좋은가 {#when-to-use}

- 즉시 commit 하지 않고도 상태 변경을 안전하게 검증해야 할 때.
- undo/redo 기능처럼 일시적인 상태 변경을 다루는 시나리오.
- 격리와 검증이 필요한 고급 상태 조작 기능을 만들 때.

### 요약 {#summary}

<tldr>

`Snapshot.takeMutableSnapshot()` 으로 mutable snapshot 을 만들면 Jetpack Compose의 상태 관리에 대해 더 정밀한 통제권을 얻게 됩니다. 상태 변경을 격리해 두고 검증·실험·검토 후에 전역 상태로 반영할 수 있어, 복잡한 상태 상호작용을 다룰 때 안전성과 유연성, 일관성을 함께 챙길 수 있습니다.

</tldr>

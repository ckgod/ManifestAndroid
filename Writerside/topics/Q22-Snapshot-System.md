# Q22) Snapshot System

## Snapshot 시스템의 목적은 무엇인가요? {#what-is-snapshot-system}

Jetpack Compose의 상태 관리는 **snapshot 시스템** 이 떠받치고 있습니다. snapshot 시스템은 애플리케이션 안의 모든 관찰 가능한(observable) 객체의 상태를 특정 시점에 그대로 캡처해 두는 메커니즘입니다. `Snapshot.takeSnapshot()` 은 현재 상태의 **읽기 전용(read-only) 스냅샷** 을 만들어, 값을 변경하지 않으면서 잠시 그 시점의 상태를 들여다보거나 활용할 수 있게 해 줍니다. 이 접근 덕분에 디버깅이나 상태 의존 기능을 구현할 때 안정성과 일관성을 동시에 챙길 수 있습니다.

Compose의 snapshot은 게임의 세이브 포인트와 비슷합니다. 특정 순간의 모든 관찰 가능한 데이터의 상태를 대표하는 한 장의 사진과 같고, snapshot을 찍는 그 순간 모든 `MutableState` 객체의 값이 동결되어 다른 곳에서 값을 바꾸더라도 이 snapshot 안에서는 그 시점의 값을 안전하게 읽을 수 있습니다.

### Snapshot.takeSnapshot()을 왜 사용하나 {#why-use-takesnapshot}

`Snapshot.takeSnapshot()` 의 주된 용도는 **현재 상태의 읽기 전용 뷰** 를 만드는 것입니다. 다음과 같은 상황에서 특히 유용합니다.

- 디버깅이나 분석 도중 상태 값을 건드리지 않고 그대로 들여다보고 싶을 때.
- 현재 상태를 기반으로 한 임시 계산이나 일회성 작업을 수행할 때.
- 멀티스레드 환경에서 상태 값을 안전하게 읽어야 할 때.

### 사용 예시 {#example}

`User` 클래스의 `name` 프로퍼티를 `MutableState` 로 두고, 현재 상태의 snapshot을 떠 본 뒤 데이터의 일관된 읽기 전용 뷰를 어떻게 얻는지 살펴봅니다.

```kotlin
class User {
    var name: MutableState<String> = mutableStateOf("")
}

fun main() {
    val user = User()

    // 초기 이름 설정
    user.name.value = "skydoves"

    // 현재 상태의 read-only snapshot 을 찍습니다.
    val snapshot = Snapshot.takeSnapshot()

    // snapshot 을 찍은 뒤 상태를 변경합니다.
    user.name.value = "Android"

    println("Current name: ${user.name.value}") // 출력: Android

    // snapshot 안으로 들어가 캡처된 값을 읽습니다.
    snapshot.enter {
        println("Snapshot name: ${user.name.value}") // 출력: skydoves
    }

    // 자원을 해제합니다.
    snapshot.dispose()
}
```
{title="SnapshotExample.kt"}

### 예시 흐름 설명 {#explanation}

1. **초기 상태**: `User` 클래스가 `MutableState` 로 뒷받침되는 `name` 프로퍼티를 가지며, 초기값은 `"skydoves"` 입니다.
2. **snapshot 찍기**: `Snapshot.takeSnapshot()` 으로 현재 상태를 캡처합니다. 이 순간 `name` 의 값은 `"skydoves"` 로 동결됩니다.
3. **상태 변경**: snapshot 을 찍은 이후 `name` 을 `"Android"` 로 변경합니다. 이 변화는 snapshot 에는 영향을 주지 않습니다.
4. **snapshot 진입**: `enter` 블록 안에서는 캡처된 상태가 다시 활성화되어, `name` 이 `"skydoves"` 로 보입니다.
5. **snapshot 해제**: 자원을 해제하기 위해 `dispose()` 를 호출합니다.

### Snapshot.takeSnapshot()의 핵심 특성 {#key-features}

1. **Read-Only**: `takeSnapshot()` 으로 만든 snapshot 은 엄격히 읽기 전용입니다. snapshot 안에서 상태를 변경하려고 하면 `IllegalStateException` 이 발생합니다.
2. **Thread Safety**: 상태가 동결되므로 동시 변경에 흔들리지 않고 값을 읽을 수 있습니다.
3. **격리(Isolation)**: snapshot 바깥에서 일어난 상태 변화는 캡처된 상태에 영향을 주지 않으며, 반대로 snapshot 도 프로그램의 현재 상태를 변경하지 않습니다.

### 읽기 전용 snapshot의 이점 {#benefits}

- **디버깅**: 상태에 대한 일관된 뷰를 제공해 이슈 분석을 쉽게 만들어 줍니다.
- **일관성**: 읽기 전용이므로 상태를 들여다보다가 실수로 값을 바꿀 위험이 없습니다.
- **단순함**: 상태를 격리해 부수 효과의 가능성을 줄여 주므로 개발 도중의 디버깅과 검증이 단순해집니다.

> **참고**: `Snapshot.takeSnapshot()` 은 사실 Compose 시스템 내부에서 이미 광범위하게 사용되고 있습니다. 예를 들어 `snapshotFlow` API의 구현 안에서도 여러 차례 활용됩니다. snapshot 시스템을 이해하고 실제로 다뤄 본 경험은 Compose에 대한 깊은 이해도를 가늠하는 좋은 지표가 되기도 합니다.

### 요약 {#summary}

<tldr>

`Snapshot.takeSnapshot()` 은 특정 시점의 앱 상태를 읽기 전용으로 캡처해 주는 도구입니다. 디버깅, 상태 분석, 또는 라이브 상태에 영향을 주지 않으면서 일관된 데이터 스냅샷이 필요한 작업에 특히 유용합니다. 이 API를 잘 활용하면 Jetpack Compose 앱을 더 안전하고 예측 가능하게 만들 수 있습니다. 더 깊은 이해를 위해서는 *Introduction to the Compose Snapshot System by Zach Klippenstein* 글을 참고할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 컴포저블에서 상태를 직접 관찰하는 대신 Snapshot.takeSnapshot() 으로 snapshot 을 찍는 편이 더 적절한 시나리오를 설명해 주세요.">

핵심은 **"UI를 다시 그리고 싶지 않은데 현재 상태의 일관된 사진은 필요한" 자리** 입니다. 컴포저블 안에서 State를 그대로 읽으면 그 컴포저블은 그 State의 변화에 반응해 리컴포지션 대상이 됩니다. 하지만 디버깅용 로그를 한 번 찍거나, 분석 이벤트를 만들기 위해 현재 화면 상태를 직렬화할 때처럼 **일회성 읽기** 가 필요할 뿐이라면, 굳이 의존성을 만들 이유가 없습니다. 이때 `Snapshot.takeSnapshot()` 으로 그 순간의 상태를 떠 두면, 의존성을 만들지 않고도 일관된 값들을 한꺼번에 읽을 수 있습니다.

또 한 가지 자주 만나는 시나리오는 **여러 상태를 함께 읽어 하나의 결과로 만들어야 할 때** 입니다. 일반 코드에서 `userName` 과 `userEmail` 을 따로 읽으면, 두 읽기 사이에 다른 스레드가 둘 중 하나만 갱신할 가능성이 늘 남아 있습니다. snapshot 을 떠 두고 `enter { ... }` 블록 안에서 두 값을 함께 읽으면, "그 순간의 한 사용자" 라는 일관성이 보장됩니다. 분석 이벤트로 보낼 페이로드를 만들거나 디버그용 dump 를 만들 때 이런 일관성이 큰 차이를 만듭니다.

마지막은 **테스트와 실험적인 상태 검증** 입니다. 다음 단계에서 다룰 mutable snapshot과 묶어 쓰면, 특정 상태에서 출발해 일련의 변경을 가해 본 뒤 결과만 살펴보고 그대로 폐기할 수 있습니다. 이 모든 사용 사례에서 공통점은 "라이브 상태와 분리된 안전한 사진 한 장이 필요하다" 는 점입니다. 컴포저블 안에서 직접 관찰은 UI 반응을 위한 것이고, snapshot은 UI와 무관한 분석·검증·로그를 위한 도구라고 구분해 두면 선택이 자연스러워집니다.

</def>
</deflist>

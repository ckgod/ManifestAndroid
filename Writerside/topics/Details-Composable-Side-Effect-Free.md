# Details: 왜 Composable 함수 안에서 비즈니스 로직을 직접 호출하면 안 되나요?

## 멀티스레드 안전을 염두에 둔 Compose 설계 {#multithreaded-safety-mindset}

Jetpack Compose는 미래의 멀티스레드 실행을 염두에 두고 설계된 프레임워크입니다. 현재의 Compose는 컴포저블을 병렬로 실행하지 않고 메인 스레드에서 동작하지만, **Compose는 컴포저블 코드를 마치 멀티스레드에서도 동작할 수 있는 것처럼 작성하기를 권장** 합니다. 이 약속을 지켜 두면 향후 Compose가 멀티 코어를 활용해 컴포저블을 병렬 실행하도록 진화하더라도, 우리 앱은 별도의 손질 없이 그 최적화의 혜택을 그대로 누릴 수 있습니다.

향후 버전의 Jetpack Compose가 백그라운드 스레드 풀에서 컴포저블을 병렬로 실행해 리컴포지션을 최적화할 가능성도 있습니다. 다만 컴포저블 함수가 thread-safe 하지 않다면 이 변화는 곧바로 버그의 원인이 됩니다. 예를 들어 컴포저블이 ViewModel과 직접 상호작용한다면, 여러 스레드에서 동시에 호출되었을 때 예상하지 못한 동작이 발생할 수 있습니다.

컴포저블 함수가 멀티스레드 환경에서도 안전하게 동작하도록 하려면 다음 원칙을 따라야 합니다.

- **부수 효과(Side Effects) 피하기**: 컴포저블 함수는 부수 효과가 없어야 합니다. 입력값을 받아 UI로 변환하기만 해야 하며, 외부 상태나 함수 스코프 안의 변수를 변경해서는 안 됩니다.
- **콜백에서 부수 효과 트리거**: 부수 효과가 필요한 동작은 `onClick` 같은 콜백 안에서 트리거해야 합니다. 이런 콜백들은 항상 UI 스레드에서 실행되므로 일관성이 보장됩니다.
- **공유 가변 상태 피하기**: 컴포저블 함수 안에서 공유 변수를 변경하는 것은 thread-safe 하지 않을 수 있으므로 피합니다.

### 부수 효과가 없는 vs 있는 컴포저블 예시 {#side-effect-examples}

다음은 부수 효과가 없는 올바른 컴포저블 예시입니다.

```kotlin
@Composable
fun SideEffectFree(text: String) {
    Card {
        Text(text = "This is a side-effect-free composable: $text")
    }
}
```
{title="SideEffectFreeComposable.kt"}

이 함수는 입력값에만 의존하며 외부 상태나 내부 변수를 변경하지 않으므로 thread-safe 합니다.

반대로 다음 예시는 부수 효과를 도입해 문제를 일으킵니다.

```kotlin
@Composable
fun SideEffect() {
    var items = 0

    Card {
        Text(text = "$items") // 이런 가변 공유 상태는 피해야 합니다.
        items++
    }
}
```
{title="SideEffectComposable.kt"}

이 컴포저블은 지역 변수 `items` 를 매 리컴포지션마다 변경합니다. 이런 쓰기는 thread-safe 하지 않으며, 여러 스레드에서 실행되면 잘못된 동작으로 이어질 수 있습니다.

### Composable 함수는 어떤 순서로도 실행될 수 있다 {#composable-execution-order}

Compose는 현재 메인 스레드에서 동작하지만, 멀티스레드를 염두에 두고 설계되어 있습니다. 이 말은 곧 컴포저블 함수가 작성된 순서대로 실행된다고 가정해서는 안 된다는 뜻입니다. 한 컴포저블 함수가 여러 자식 컴포저블을 호출할 때, Compose는 컨텍스트에 따라 어떤 자식을 먼저 렌더링할지 우선순위를 다르게 가져갈 수 있고, 따라서 자식들의 실행 순서가 항상 위에서 아래로 보장되지는 않습니다.

예를 들어 한 행을 렌더링하는 다음 코드를 봅시다.

```kotlin
@Composable
fun TabLayout() {
    Row {
        FirstComposable { /* ... */ }
        SecondComposable { /* ... */ }
        ThirdComposable { /* ... */ }
    }
}
```
{title="ComposableOrder.kt"}

여기서 `FirstComposable`, `SecondComposable`, `ThirdComposable` 은 어떤 순서로도 실행될 수 있습니다. 정확성을 유지하려면 각 컴포저블이 자족적이어야 하고, 공유 전역 변수를 수정하는 것 같은 부수 효과에 의존해서는 안 됩니다. 예컨대 `FirstComposable` 이 어떤 전역 변수를 바꿔 두고 `SecondComposable` 이 그 값을 사용하는 식의 의존을 두면, 미래의 병렬 실행 모델에서 곧바로 깨집니다.

### 요약 {#summary}

<tldr>
컴포저블 함수는 현재 단일 스레드에서 실행되더라도, 향후 멀티스레드 실행을 전제로 작성하는 것이 권장됩니다. 부수 효과가 없는 컴포저블을 작성하고 가변 공유 상태를 피하면, 정확성과 thread-safety 가 자연스럽게 따라옵니다. 부수 효과는 콜백에서 트리거하고, 비즈니스 로직은 컴포저블 본문이 아니라 ViewModel 같은 곳으로 끌어올려 두면 현재 성능과 안정성도 좋아지고 미래 최적화에도 대비할 수 있습니다. 더 깊은 이해를 위해서는 *Thinking in Compose* 가이드를 참고할 수 있습니다.
</tldr>

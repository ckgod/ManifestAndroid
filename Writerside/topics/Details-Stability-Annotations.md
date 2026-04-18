# Details: Stability 어노테이션 (@Stable, @Immutable)

## Stability 어노테이션이란? {#what-are-stability-annotations}

Stability 어노테이션은 클래스의 stability 를 개발자가 명시적으로 알려 줌으로써 Compose 컴파일러가 리컴포지션을 최적화할 수 있게 해 주는 도구입니다. [compose-runtime 라이브러리](https://developer.android.com/jetpack/androidx/releases/compose-runtime)가 제공하는 두 가지 핵심 어노테이션이 `@Immutable` 과 `@Stable` 이며, 각각의 목적과 적용 대상이 다릅니다.

### @Immutable {#immutable}

`@Immutable` 어노테이션은 클래스가 **완전히 불변** 임을 표시합니다. 단순히 `val` 만 사용하는 것보다 더 강한 약속을 컴파일러에 제공하는 셈입니다. 클래스에 이 어노테이션을 붙이면 컴파일러는 그 안의 모든 프로퍼티를 불변으로 간주하므로, 이 클래스에 의존하는 컴포저블 함수의 리컴포지션을 안전하게 **건너뛸** 수 있습니다.

#### 핵심 특성

- 클래스의 모든 프로퍼티가 불변으로 간주되어야 합니다.
- 가변 프로퍼티가 없는, 읽기 전용이거나 이미 불변인 data class·모델에 주로 사용합니다.
- 클래스 내부 상태가 절대 변하지 않음을 보장하므로 최적화가 단순해집니다.

#### 예시

```kotlin
@Immutable
data class User(val id: Int, val items: List<String>)
```
{title="ImmutableExample.kt"}

위 예제에서 `id` 는 원시 타입이라 stable 하지만, `items` 는 List 타입이라 본래 unstable 한 데이터 타입입니다. 그 결과 `User` 클래스 전체가 unstable 로 분류됩니다. 그러나 개발자가 런타임에 이 프로퍼티들이 논리적으로 변하지 않을 것임을 알고 있다면, `@Immutable` 을 붙여 명시적으로 stable 임을 선언할 수 있습니다.

### @Stable {#stable}

`@Stable` 어노테이션은 프로퍼티가 불변이거나, 또는 가변성이 통제되어 리컴포지션에 영향을 주지 않는 클래스에 사용합니다. `@Immutable` 보다 약하지만 여전히 강한 약속이며, 클래스 자체는 **stable** 로 간주되지만 프로퍼티가 변할 수 있다는 가능성을 열어 둡니다. 다만 그 변화는 통제되어 있고 Compose 런타임 입장에서는 안전한 형태여야 합니다.

따라서 `@Stable` 은 클래스 전체로는 stable 로 분류되지 않지만 public 프로퍼티가 불변인 인터페이스나 클래스에 잘 어울립니다. 예를 들어 Jetpack Compose의 `State` 인터페이스는 외부에 불변 `value` 프로퍼티를 노출하지만, 내부적으로는 `MutableState` 같은 구현체가 setValue 함수를 통해 값을 갱신합니다.

#### 핵심 특성

- 일부 가변 프로퍼티를 허용하되, 클래스 전체의 stability 는 유지되어야 합니다.
- 가변성이 내부적으로 잘 통제되는 클래스에 적합합니다.
- 완전 불변이 현실적이지 않은 경우에 유연성을 제공합니다.

#### 예시

```kotlin
@Stable
interface State<out T> {
    val value: T
}

@Stable
interface MutableState<T> : State<T> {
    override var value: T
    operator fun component1(): T
    operator fun component2(): (T) -> Unit
}
```
{title="StableInterface.kt"}

`MutableState` 로 만들어진 `State` 인스턴스는 `getValue` 함수의 결과로 항상 같은 값을 반환합니다. 같은 값을 setValue 로 다시 설정해도 결과의 일관성이 유지됩니다. 위 코드에서는 `State` 와 `MutableState` 인터페이스 모두 `@Stable` 이 붙어 있습니다.

함수에 `@Stable` 이 붙은 사례도 있습니다. 이는 그 함수가 반환하는 값이 Compose 컴파일러 입장에서 stable 한 것으로 간주된다는 표시이며, 효율적인 리컴포지션을 보장하기 위한 장치입니다.

```kotlin
@Stable
fun Modifier.clipScrollableContainer(orientation: Orientation) =
    then(
        if (orientation == Orientation.Vertical) {
            Modifier.clip(VerticalScrollableClipShape)
        } else {
            Modifier.clip(HorizontalScrollableClipShape)
        }
    )
```
{title="clipScrollableContainer.kt"}

### @Immutable과 @Stable의 차이 {#differences}

두 어노테이션의 차이를 표로 정리하면 다음과 같습니다.

| 측면 | @Immutable | @Stable |
|---|---|---|
| **불변성 요구** | 모든 프로퍼티가 불변으로 간주되어야 함 | 일부 프로퍼티에 통제된 가변성을 허용 |
| **사용 시점** | 불변으로 다뤄져야 하는 데이터 모델·구성 | UI 상태처럼 통제된 가변성을 가진 클래스 |
| **리컴포지션 동작** | 동일 파라미터에 대해 의존 컴포저블의 리컴포지션을 완전히 스킵 | 가변 프로퍼티가 바뀌면 리컴포지션이 트리거될 수 있음 |

`@Immutable` 은 보통 네트워크 응답이나 DB 엔티티처럼 **I/O 결과로부터 만들어진 도메인 모델** 에 사용됩니다. 이런 모델들은 인터페이스나 unstable 클래스 참조를 포함하면 unstable 로 분류될 수 있는데, `@Immutable` 을 붙이면 **Compose 컴파일러가 클래스를 불변으로 취급** 하여 안정성을 확보하고 리컴포지션을 최적화합니다. 예시는 다음과 같습니다.

```kotlin
@Immutable
public data class User(
    public val id: String,
    public val nickname: String,
    public val profileImages: List<String>,
)
```
{title="ImmutableExample.kt"}

반면 `@Stable` 은 다양한 구현이 가능하고 내부 가변 상태를 가질 수 있는 인터페이스에 적용하기 좋습니다. 다음 예시를 참고할 수 있습니다.

```kotlin
@Stable
interface UiState<T : Result<T>> {
    val value: T?
    val exception: Throwable?

    val hasSuccess: Boolean
        get() = exception == null
}
```
{title="StableExample.kt"}

`@Stable` 어노테이션은 `UiState` 클래스를 stable 로 표시함으로써, Jetpack Compose가 최적화된 리컴포지션과 지능적인 스킵을 활용할 수 있게 합니다. 결과적으로 불필요한 리컴포지션을 최소화하면서 UI 갱신의 효율을 끌어올릴 수 있습니다.

### 요약 {#summary}

<tldr>

적절한 stability 어노테이션을 적용하면 Jetpack Compose 앱을 보다 효과적으로 최적화할 수 있습니다. 완전 불변으로 다뤄져야 하는 클래스에는 `@Immutable` 을, 통제된 가변성을 가지면서도 예측 가능한 동작을 보장하는 클래스에는 `@Stable` 을 사용하면 됩니다. 두 어노테이션을 정확히 이해하고 활용하면 앱의 성능과 유지보수성을 크게 향상시킬 수 있습니다.

</tldr>

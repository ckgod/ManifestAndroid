# Details: Compose Compiler와 Composer

## Compose Compiler는 어떤 변환을 수행하나요? {#what-compose-compiler-does}

**Compose Compiler** 는 빌드 시점에 `@Composable` 함수의 IR(Intermediate Representation)을 최적화된 코드로 변환합니다. 이 변환은 UI 렌더링과 상태 관리를 효율적으로 처리하기 위한 핵심 단계이며, Compose의 선언형 UI 패러다임을 가능하게 만들어 주는 근간입니다. 이 과정에서 가장 중요한 부품이 바로 컴포저블의 상태를 추적·관리하는 **Composer** 입니다.

### Composable 함수의 변환 {#transformation-of-composable}

함수에 `@Composable` 을 붙이면 Compose 컴파일러는 그 함수의 구조를 수정해 모든 컴포저블 함수에 암묵적인 `Composer` 파라미터를 추가합니다. 이 파라미터는 컴포저블 함수와 Compose Runtime을 잇는 다리 역할을 하며, 런타임이 UI 상태, 리컴포지션, 그 외 핵심 기능들을 효율적으로 관리할 수 있게 해 줍니다.

예를 들어 다음과 같은 단순한 컴포저블이 있다고 해 봅시다.

```kotlin
@Composable
fun Greeting(name: String) {
    Text("Hello, $name!")
}
```
{title="Greeting.kt"}

Compose 컴파일러는 이 함수를 개념적으로 다음과 같은 형태로 변환합니다.

```kotlin
fun Greeting(name: String, composer: Composer, key: Int) {
    composer.startRestartGroup(key)
    val nameArg = composer.changed(name)
    if (nameArg) {
        Text("Hello, $name!")
    }
    composer.endRestartGroup()
}
```
{title="Composer.kt"}

이 변환을 통해 런타임이 입력 파라미터(여기서는 `name`)의 변화 여부에 따라 리컴포지션이 필요한지 판단할 수 있는 후크가 도입됩니다. 이런 훅 덕분에 Compose는 변경되지 않은 UI 부분의 리컴포지션을 건너뛰며 성능을 최적화할 수 있습니다.

### Composer의 역할 {#role-of-composer}

[Composer](https://cs.android.com/androidx/platform/frameworks/support/+/androidx-main:compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/Composer.kt)는 Compose Runtime의 저수준 API로, 중심 상태 관리자 역할을 맡습니다. Compose Kotlin 컴파일러 플러그인이 직접 타깃으로 삼는 인터페이스이며, 코드 생성 헬퍼들도 이 Composer를 통해 동작합니다.

Composer가 책임지는 일은 다음과 같습니다.

1. **상태 관리**: 상태를 추적하고, 입력이 바뀌었을 때 컴포저블 함수가 올바르게 리컴포즈되도록 보장합니다.
2. **UI 계층 구성**: UI 트리 구조를 유지하면서 상태가 바뀔 때 노드들을 효율적으로 갱신합니다.
3. **최적화**: 입력 파라미터의 변화를 분석하여, UI 트리 중 어느 부분만 다시 컴포즈되면 되는지 결정합니다.
4. **리컴포지션 제어**: 특정 컴포저블에 대해 리컴포지션을 시작·건너뛰기·종료하는 흐름을 조율합니다.

Composer 덕분에 리컴포지션은 **점진적(incremental)** 으로 동작합니다. 즉 UI 트리 전체가 아니라 정말 필요한 부분만 갱신되므로, 불필요한 계산이 줄고 성능이 개선됩니다.

### 요약 {#summary}

<tldr>

Compose 컴파일러는 `@Composable` 함수에 `Composer` 와 그 외 필요한 파라미터를 주입함으로써, Compose Runtime이 UI 상태와 리컴포지션을 효율적으로 다룰 수 있게 만들어 줍니다. Composer는 상태 추적, 리컴포지션, UI 갱신을 모두 책임지는 런타임의 중추이며, 컴파일러와 런타임의 이런 통합이 Jetpack Compose를 모던하고 효율적인 선언형 UI 프레임워크로 만들어 주는 토대입니다.

</tldr>

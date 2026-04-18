# Q4) Composable 함수의 내부 동작

## Composable 함수는 내부적으로 어떻게 동작하나요? {#how-composable-works-internally}

Jetpack Compose는 선언형 UI를 구성하는 빌딩 블록으로 `@Composable` 함수를 도입했습니다. 겉으로는 평범한 Kotlin 함수처럼 보이지만, 내부적으로는 **Compose Compiler 플러그인** 이 일반 Kotlin 코드를 반응형·상태 주도 UI 갱신을 지원하는 구조로 변환해 줍니다.

### 컴파일러 변환 {#compiler-transformation}

`@Composable` 어노테이션이 붙은 함수를 만나면 Compose Compiler 플러그인이 Kotlin 컴파일 과정에 끼어듭니다. 일반 Kotlin 함수처럼 처리하지 않고, 추가 파라미터와 로직을 주입해 Compose의 반응형 시스템이 동작할 수 있게 만듭니다. 이 과정에서 가장 핵심이 되는 것은 컴포지션 상태를 추적하고 UI 상태가 바뀔 때 리컴포지션을 처리하는 숨겨진 `Composer` 객체입니다.

예를 들어 다음과 같은 단순한 컴포저블이 있다고 가정해 봅시다.

```kotlin
@Composable
fun MyComposable() {
    Text("Hello, Compose!")
}
```
{title="MyComposable.kt"}

내부적으로는 `Composer` 객체와 상태 관리용 메타데이터가 포함된 형태로 변환됩니다. 위 예제를 자바 바이트코드로 디컴파일해 보면 대략 다음과 같은 모습이 됩니다.

```java
private static final void MyComposable(Composer $composer, int $changed) {
    $composer = $composer.startRestartGroup(1017251926);
    ComposerKt.sourceInformation($composer, "C(MyComposable)...");

    if ($changed == 0 && $composer.getSkipping()) {
        $composer.skipToGroupEnd();
    } else {
        if (ComposerKt.isTraceInProgress()) {
            ComposerKt.traceEventStart(...);
        }

        TextKt.Text("Hello, Compose!", ..., $composer, 6, 0, 262142);

        if (ComposerKt.isTraceInProgress()) {
            ComposerKt.traceEventEnd();
        }
    }

    ScopeUpdateScope var10000 = $composer.endRestartGroup();
    if (var10000 != null) {
        var10000.updateScope(MainActivityKt::MyComposable$lambda$0);
    }
}
```
{title="MyComposable-decompiled.java"}

평범했던 함수가 `startRestartGroup`/`endRestartGroup`, `skipToGroupEnd` 같은 호출로 둘러싸인 구조로 바뀐 것을 볼 수 있습니다. 바로 이 변환 덕분에 Compose 런타임이 어느 함수가 다시 호출되어야 하는지를 결정하고, 상태가 바뀌지 않은 부분은 건너뛸 수 있습니다.

### Composition과 Recomposition {#composition-and-recomposition}

`@Composable` 함수의 수명 주기를 관리하는 것은 **Compose Runtime** 입니다. **Composition 단계** 에서 런타임은 컴포저블 함수를 실행하면서 UI 트리를 만들어 내고, 이를 **슬롯 테이블(Slot Table)** 이라는 자료구조에 저장합니다. 슬롯 테이블은 Compose가 UI를 효율적으로 관리하고 갱신하기 위한 핵심 자료구조입니다.

상태가 바뀌면 **리컴포지션** 이 트리거됩니다. 전체 UI 트리를 처음부터 다시 만드는 대신, 슬롯 테이블을 활용해 어느 부분이 갱신되어야 하는지 정확히 짚어내고 그 컴포저블 함수만 다시 실행합니다. 덕분에 화면에 변화가 없는 영역은 비용을 들이지 않고 그대로 유지됩니다.

### remember와 상태 관리 {#remember-and-state}

상태를 관리하기 위해 Compose는 `remember`와 `State` 같은 API를 제공합니다. 이들은 런타임·컴파일러와 긴밀하게 협력해 리컴포지션을 가로질러 상태를 보존하고, UI가 항상 데이터 모델과 일치하도록 유지합니다.

```kotlin
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("Count: $count")
    }
}
```
{title="Counter.kt"}

여기서 `remember` 는 `count` 상태가 리컴포지션이 일어나는 동안에도 메모리에서 사라지지 않도록 보존해 주고, `mutableStateOf` 는 값이 바뀌었음을 Compose에 알려 리컴포지션을 트리거합니다.

### 요약 {#summary}

<tldr>

`@Composable` 함수는 Compose Compiler 플러그인을 통해 Kotlin 코드가 반응형 UI 컴포넌트로 변환되어 Compose Runtime이 관리할 수 있는 형태로 만들어집니다. 슬롯 테이블 기반의 효율적인 트리 관리, `remember`/`State` 같은 상태 도구가 결합되어, 상태 변화에 따른 효율적인 렌더링과 동적 UI 갱신이 가능해집니다. 이 구조가 Jetpack Compose가 선언형이면서도 효율적인 UI 프레임워크일 수 있는 이유입니다. 더 깊이 들여다보고 싶다면 *Android Developers: Under the hood of Jetpack Compose* 글을 참고할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 함수에 @Composable 어노테이션을 붙이면 내부적으로 어떤 일이 일어나나요?">

겉으로 보이는 변화는 거의 없지만, 컴파일 시점에 함수의 시그니처와 본문이 모두 달라집니다. Compose Compiler 플러그인이 Kotlin 컴파일러 위에 얹혀 동작하면서, 어노테이션이 붙은 함수마다 숨겨진 `Composer` 파라미터와 변경 추적용 비트마스크 파라미터(`$changed`)를 추가합니다. 그래서 일반 Kotlin 함수처럼 호출되는 것처럼 보이지만 실제로는 매 호출마다 현재 컴포지션의 상태와 함께 호출되는, 런타임의 협력자가 됩니다.

본문 자체도 다시 쓰입니다. 컴파일러는 함수 시작과 끝에 `startRestartGroup`/`endRestartGroup` 같은 호출을 끼워 넣어, 이 함수가 어떤 그룹의 일부인지를 슬롯 테이블에 기록하도록 만듭니다. 또한 입력 파라미터가 바뀌지 않았고 함수가 skippable 하다면 `skipToGroupEnd`로 본문 실행 자체를 건너뛰도록 분기를 추가합니다. 이 분기 덕분에 부모가 다시 호출되더라도 자식 컴포저블이 모두 다시 실행되지는 않으며, 변경된 영역만 효율적으로 갱신됩니다.

마지막으로 컴파일러는 함수의 안정성(stability)과 종류(restartable/skippable/movable 등)를 분석해 분류해 둡니다. 이 분류는 런타임의 리컴포지션 결정에 직접 사용되며, 잘못 사용된 unstable 파라미터나 불필요한 람다 캡처 같은 문제는 같은 단계에서 컴파일러 리포트를 통해 드러납니다. 즉 `@Composable` 어노테이션은 단순한 마커가 아니라 "이 함수를 Compose 런타임이 추적·재실행·스킵할 수 있는 단위로 바꿔 달라"는 컴파일러 지시문에 가깝습니다.

</def>
</deflist>

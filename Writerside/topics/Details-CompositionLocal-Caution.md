# Details: CompositionLocal을 신중하게 사용해야 하는 이유

## 두 종류의 CompositionLocal {#two-kinds-of-compositionlocal}

CompositionLocal은 UI 트리를 따라 데이터를 암묵적으로 내려보낼 수 있게 해 주는 메커니즘입니다. 재사용성과 데이터 전파를 단순화해 주지만, 잘못 사용하면 불필요한 리컴포지션을 유발해 성능에 영향을 줄 수 있습니다. Jetpack Compose는 CompositionLocal을 만드는 두 가지 API — `compositionLocalOf` 와 `staticCompositionLocalOf` — 를 제공하며, 둘의 차이를 이해하는 것이 효율적인 상태 관리에 직결됩니다.

### compositionLocalOf: 동적 상태와 세밀한 리컴포지션 {#compositionlocalof}

`compositionLocalOf` 는 동적 CompositionLocal 입니다. 값이 바뀌면 그 값을 **읽는** 컴포저블만 리컴포지션됩니다. 자주 바뀌면서도 갱신 범위는 좁게 유지하고 싶은 상태에 적합합니다.

```kotlin
val LocalUser = compositionLocalOf { "skydoves" }

@Composable
fun UserScreen() {
    var user by remember { mutableStateOf("skydoves") }

    Column {
        Button(onClick = { user = "android" }) {
            Text("Change User")
        }
        CompositionLocalProvider(LocalUser provides user) {
            UserProfile()
        }
    }
}

@Composable
fun UserProfile() {
    Text("User: ${LocalUser.current}")
}
```
{title="DynamicCompositionLocal.kt"}

#### 동작 방식

- `LocalUser` 는 리컴포지션 동안 변하는 동적 값을 보관합니다.
- 버튼이 눌리면 `UserScreen` 이 값을 갱신하고, **`UserProfile` 만** 리컴포지션되어 성능이 최적화됩니다.

### staticCompositionLocalOf: 정적 값에 효율적 {#staticcompositionlocalof}

`compositionLocalOf` 와 달리 `staticCompositionLocalOf` 는 컴포지션 안에서의 읽기를 추적하지 않습니다. 대신 제공된 값이 바뀌면 Provider 가 설정된 콘텐츠 블록 **전체** 가 무효화되어 더 넓은 범위의 리컴포지션이 일어납니다.

```kotlin
val LocalThemeColor = staticCompositionLocalOf { Color.Black }

@Composable
fun ThemedScreen() {
    var themeColor by remember { mutableStateOf(Color.Blue) }

    Column {
        Button(onClick = { themeColor = Color.Green }) {
            Text("Change Theme")
        }
        CompositionLocalProvider(LocalThemeColor provides themeColor) {
            ThemedContent()
        }
    }
}

@Composable
fun ThemedContent() {
    Box(modifier = Modifier.background(LocalThemeColor.current).size(100.dp))
}
```
{title="StaticCompositionLocal.kt"}

#### 동작 방식

- `LocalThemeColor` 는 정적 테마 색상을 보관합니다.
- `themeColor` 가 갱신되면 `CompositionLocalProvider` 블록 전체가 리컴포지션됩니다.
- `compositionLocalOf` 와 달리 그 값을 사용하는 특정 컴포저블만 골라서 리컴포지션하지 않으므로, 자주 바뀌지 않는 전역 값(테마, 구성)에 적합합니다.

### 리컴포지션 측면에서의 비교 {#recomposition-considerations}

CompositionLocal을 잘못 사용하면 불필요한 리컴포지션이 발생해 성능에 영향을 줍니다. 두 API의 차이를 표로 정리하면 다음과 같습니다.

| API | 리컴포지션 동작 | 적합한 사용 사례 |
|---|---|---|
| `compositionLocalOf` | `current` 가 호출되는 곳만 다시 평가 | 자주 바뀌는 상태(예: 사용자 환경, 부분 UI 갱신) |
| `staticCompositionLocalOf` | Provider 블록 전체 리컴포지션 | 거의 변하지 않는 전역 값(예: 테마, 구성) |

성능을 최적화하기 위한 권장 가이드는 다음과 같습니다.

- **거의 변하지 않는 전역 값에는 `staticCompositionLocalOf`** 를 사용해 과도한 리컴포지션을 피합니다.
- **빈번히 변하지만 영향 범위는 좁은 상태에는 `compositionLocalOf`** 를 사용해 정말 필요한 컴포저블만 갱신되도록 합니다.
- **매우 동적인 데이터에는 CompositionLocal 자체를 피합니다.** 이 자리에는 `remember` 나 `State` 로 로컬 UI 상태를 관리하는 편이 더 효율적입니다.

### 요약 {#summary}

<tldr>

CompositionLocal 은 Compose 계층 안에서 데이터를 전달하는 데 유용한 도구이지만, 불필요한 리컴포지션을 유발하지 않도록 신중하게 사용해야 합니다. 자주 바뀌는 값에는 `compositionLocalOf` 가 세밀한 통제를, 안정적이고 전역적인 구성에는 `staticCompositionLocalOf` 가 효율을 가져다 줍니다. 시나리오에 맞게 적절한 API를 골라 사용하면 더 효율적이고 성능 좋은 Compose 앱을 만들 수 있습니다.

</tldr>

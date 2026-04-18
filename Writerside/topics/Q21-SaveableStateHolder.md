# Q21) SaveableStateHolder

## SaveableStateHolder는 무엇인가요? {#what-is-saveablestateholder}

Jetpack Compose에서 동적이거나 다중 화면(multi-screen) UI를 다루다 보면, 내비게이션이나 구성 변경(configuration change) 동안 화면 각각의 상태를 저장하고 복원하는 작업이 까다롭게 느껴지는 순간이 옵니다. 바로 이 자리에서 [SaveableStateHolder](https://developer.android.com/reference/kotlin/androidx/compose/runtime/saveable/SaveableStateHolder)가 제 역할을 합니다. 컴포저블이 일시적으로 컴포지션에서 빠졌다가(예: 다른 화면으로 이동) 다시 들어오는 경우에도 상태를 그대로 유지할 수 있게 해 줍니다.

**SaveableStateHolder** 는 `rememberSaveable` 과 짝을 이루는 Compose Runtime API로, 고유한 키를 기준으로 컴포저블의 상태를 저장·복원합니다. 컴포저블이 컴포지션에서 빠지면 상태가 자동으로 저장되고, 다시 컴포지션에 들어오면 그 키에 묶인 상태가 자동으로 복원됩니다.

### 예시: 내비게이션과 함께 사용하기 {#example-with-navigation}

다음 예시는 내비게이션 시나리오에서 SaveableStateHolder를 사용해 화면 상태를 관리하는 모습을 보여 줍니다. 각 화면이 자신의 상태를 독립적으로 유지하므로, 화면을 오갈 때마다 입력값이나 카운터가 그대로 유지됩니다.

```kotlin
@Composable
fun <T : Any> Navigation(
    currentScreen: T,
    modifier: Modifier = Modifier,
    content: @Composable (T) -> Unit
) {
    // SaveableStateHolder 를 만듭니다.
    val saveableStateHolder = rememberSaveableStateHolder()

    Box(modifier) {
        // 현재 화면 콘텐츠를 SaveableStateProvider 로 감쌉니다.
        saveableStateHolder.SaveableStateProvider(currentScreen) { content(currentScreen) }
    }
}

@Composable
fun SaveableStateHolderExample() {
    var screen by rememberSaveable { mutableStateOf("screen1") }

    Column {
        // 내비게이션 버튼
        Row(horizontalArrangement = Arrangement.SpaceEvenly) {
            Button(onClick = { screen = "screen1" }) { Text("Go to screen1") }
            Button(onClick = { screen = "screen2" }) { Text("Go to screen2") }
        }

        // SaveableStateHolder 와 결합한 내비게이션
        Navigation(screen, Modifier.fillMaxSize()) { currentScreen ->
            if (currentScreen == "screen1") {
                Screen1()
            } else {
                Screen2()
            }
        }
    }
}

@Composable
fun Screen1() {
    var counter by rememberSaveable { mutableStateOf(0) }
    Column {
        Text("Screen 1")
        Button(onClick = { counter++ }) {
            Text("Counter: $counter")
        }
    }
}

@Composable
fun Screen2() {
    var text by rememberSaveable { mutableStateOf("") }
    Column {
        Text("Screen 2")
        TextField(
            value = text,
            onValueChange = { text = it },
            label = { Text("Enter text") }
        )
    }
}
```
{title="SaveableStateHolderNavigation.kt"}

### 예시의 핵심 개념 {#key-concepts}

1. **Navigation 래퍼**: `Navigation` 컴포저블은 현재 화면을 받아 `SaveableStateProvider` 로 감쌉니다. 이를 통해 각 화면의 상태가 화면 키에 묶여 독립적으로 저장·복원됩니다.
2. **상태 유지(State Retention)**: `Screen1` 과 `Screen2` 는 각각 `rememberSaveable` 로 자신의 상태를 보존합니다. 예를 들어 Screen1은 카운터를, Screen2는 텍스트 입력을 유지합니다.
3. **동적 상태 처리**: 내비게이션 버튼으로 화면을 오갈 때 각 화면의 상태가 보존되어 데이터 손실 없이 자연스럽게 화면 전환이 이뤄집니다.

### SaveableStateHolder의 장점 {#advantages}

- **화면 간 상태 보존**: 다른 화면으로 빠져나가더라도 각 화면의 상태가 유지됩니다.
- **단순한 상태 관리**: 상태 저장/복원 동작을 자동으로 처리해 보일러플레이트를 줄여 줍니다.
- **구성 변경 처리**: `rememberSaveable` 과 함께 동작하면서 화면 회전 같은 구성 변경 시점에도 상태를 안전하게 보존합니다.

### 요약 {#summary}

<tldr>

**SaveableStateHolder** 를 내비게이션 흐름에 끼워 넣으면, 각 화면의 상태를 별도의 복잡한 코드 없이 보존할 수 있습니다. 다중 화면 앱에서 사용자 경험과 상태 보존을 동시에 챙기는 데 유용한 도구입니다. [Jetpack Navigation Compose](https://developer.android.com/develop/ui/compose/navigation)를 사용하는 환경에서도, 화면 전환과 구성 변경을 가로질러 다양한 UI 상태를 유지해야 할 때 `SaveableStateProvider` 가 여전히 의미 있는 역할을 합니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Jetpack Navigation 라이브러리를 쓰지 않고 탭 UI를 만들 때, 각 탭의 스크롤 위치나 입력 상태를 화면 전환에도 유지하려면 어떻게 구현하시겠습니까?">

가장 자연스러운 접근은 **탭 컨테이너 위에 `rememberSaveableStateHolder` 를 두고, 각 탭의 콘텐츠를 `SaveableStateProvider(key = tabId)` 로 감싸는 것** 입니다. 사용자가 다른 탭으로 이동하면 현재 탭 콘텐츠는 컴포지션에서 빠지지만, 그 시점의 `rememberSaveable` 상태들이 탭 ID 키 아래에 보관됩니다. 다시 그 탭으로 돌아오면 같은 키로 SaveableStateProvider 가 만들어지면서 보관해 두었던 상태를 그대로 꺼내 쓰는 형태입니다. 본문 예시의 `Navigation` 컴포저블이 정확히 이 패턴이며, 탭 화면에서는 `currentScreen` 자리에 `selectedTabId` 만 넘기면 그대로 재사용할 수 있습니다.

탭마다 보존하고 싶은 상태(예: 스크롤 위치, 텍스트 입력)는 그 탭 콘텐츠 안에서 `rememberSaveable` 또는 `rememberLazyListState` 같은 saveable 한 API로 만드는 것이 핵심입니다. SaveableStateHolder는 결국 **`rememberSaveable` 류 API의 저장 결과를 키별로 묶어 두는 컨테이너** 이므로, 안에서 사용하는 상태가 saveable 형태가 아니면 효과를 보지 못합니다. `LazyListState` 의 경우 기본 saver 가 제공되어 있고, 직접 만든 데이터 클래스라면 `rememberSaveable(saver = ...)` 로 saver 를 명시해 주면 됩니다.

마지막으로 두 가지 실수 포인트만 챙기면 됩니다. 첫째, **각 탭의 키는 안정적이고 고유해야** 합니다. 탭이 동적으로 추가되는 UI라면 인덱스가 아니라 탭 ID나 라벨 같은 안정적인 식별자를 키로 써야 탭 순서가 바뀌었을 때 상태가 엉키지 않습니다. 둘째, 더 이상 보여 줄 일이 없는 탭의 상태는 `saveableStateHolder.removeState(key)` 로 명시적으로 정리해 주면 메모리 사용을 통제할 수 있습니다. 이 두 가지를 지키면 Jetpack Navigation 없이도 충분히 안정적인 탭 UI 상태 보존을 만들 수 있습니다.

</def>
</deflist>

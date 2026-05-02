# Q37) Compose 화면 내비게이션

## Compose에서 화면 사이를 어떻게 내비게이션하나요? {#how-to-navigate-screens}

내비게이션은 모던 Android 개발에서 핵심적인 부분입니다. 최근에는 단일 Activity 구조가 권장되면서 XML 기반 프로젝트에서도 내비게이션의 비중이 더 커졌습니다. Jetpack Compose에는 Fragment 개념이 없으므로, 내비게이션 스택과 컨트롤러, UI 상태를 관리해 줄 별도의 내비게이션 시스템이 필요합니다. Compose 프로젝트에서 내비게이션을 구현하는 방식은 크게 두 가지로, **수동 내비게이션 관리** 와 스택 처리·상태 보존을 단순화해 주는 **Jetpack Compose Navigation 라이브러리** 사용입니다.

### 수동 내비게이션 {#manual-navigation}

`SaveableStateHolder` 와 `rememberSaveable` 을 활용해 직접 내비게이션 시스템을 만들 수도 있습니다. `SaveableStateHolder` 는 고유 키를 기반으로 컴포저블의 상태를 저장·복원해 주는 Compose Runtime API입니다. 컴포저블이 컴포지션에서 빠지면 상태가 자동 저장되고, 다시 들어오면 그 키에 묶인 상태가 자동으로 복원됩니다.

다음 예시는 내비게이션 시나리오에서 `SaveableStateHolder` 로 상태를 관리하는 모습을 보여 줍니다. 각 화면이 독립적으로 자기 상태를 보존하므로 화면을 오갈 때 상태가 그대로 유지됩니다.

```kotlin
@Composable
fun &lt;T : Any&gt; Navigation(
    currentScreen: T,
    modifier: Modifier = Modifier,
    content: @Composable (T) -&gt; Unit
) {
    val saveableStateHolder = rememberSaveableStateHolder()

    Box(modifier) {
        // 화면 전환 시 자연스러운 트랜지션을 적용합니다.
        AnimatedContent(currentScreen) {
            // 현재 화면 콘텐츠를 SaveableStateProvider 로 감쌉니다.
            saveableStateHolder.SaveableStateProvider(it) { content(it) }
        }
    }
}

@Composable
fun SaveableStateHolderExample() {
    var screen by rememberSaveable { mutableStateOf("screen1") }

    Column {
        Row(horizontalArrangement = Arrangement.SpaceEvenly) {
            Button(onClick = { screen = "screen1" }) { Text("Go to screen1") }
            Button(onClick = { screen = "screen2" }) { Text("Go to screen2") }
        }

        Navigation(screen, Modifier.fillMaxSize()) { currentScreen ->
            if (currentScreen == "screen1") Screen1() else Screen2()
        }
    }
}
```
{title="SaveableStateHolderNavigation.kt"}

수동 내비게이션은 작은 화면 구성에서는 충분히 동작하지만, 실제 앱의 내비게이션은 훨씬 복잡합니다. 위로 이동하기, 특정 화면으로 점프, 딥 링크 같은 시나리오는 일관된 처리를 위한 전용 시스템이 필요합니다. 또한 Jetpack ViewModel 의 수명 주기는 내비게이션 상태에 묶여 있고, DI 프레임워크와 결합되면 수동 관리는 더 까다로워집니다. 따라서 복잡한 사용 사례에서는 Jetpack Compose Navigation 라이브러리를 사용하는 편이 권장됩니다.

### Jetpack Compose Navigation {#jetpack-compose-navigation}

Jetpack Compose는 Compose 전용의 [navigation 라이브러리](https://developer.android.com/develop/ui/compose/navigation)를 제공합니다. Jetpack Navigation 시스템의 인프라를 그대로 활용하면서, 컴포저블 화면 사이의 내비게이션을 매끄럽게 다룰 수 있게 해 줍니다. 구조화된 내비게이션 관리, 상태 처리, 딥 링크, 안전한 인자(safe arguments) 까지 포괄해 모던 Android 앱의 내비게이션을 견고하게 만들어 줍니다.

Compose Navigation 시스템은 세 가지 핵심 구성 요소로 이뤄집니다.

- **NavHost**: 내비게이션 그래프를 정의하고, 컴포저블 화면을 라우트와 연결합니다.
- **NavController**: 내비게이션 스택을 관리하고, 목적지 사이의 이동을 처리합니다.
- **Composable Destinations**: 내비게이션 그래프 안의 개별 화면들입니다.

#### 1. NavHost로 내비게이션 정의하기 {#navhost}

`NavHost` 가 내비게이션 그래프를 관리합니다. 시작 목적지(start destination)와 화면들 사이의 라우트를 정의합니다.

```kotlin
sealed interface PokedexScreen {

    @Serializable
    object Home : PokedexScreen

    @Serializable
    object Details : PokedexScreen
}

@Composable
fun AppNavHost(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController(),
) {
    NavHost(
        modifier = modifier,
        navController = navController,
        startDestination = PokedexScreen.Home
    ) {
        composable<PokedexScreen.Home> {
            HomeScreen(
                onNavigateToDetails = { navController.navigate(route = PokedexScreen.Details) }
            )
        }
        composable<PokedexScreen.Details> {
            DetailsScreen()
        }
    }
}
```
{title="AppNavHost.kt"}

`NavHost` 가 사용 가능한 목적지를 정의하고, Home 을 시작 목적지로 지정합니다. `composable<Home>` 과 `composable<Details>` 가 그래프 안의 개별 화면을 표현합니다. `NavController` 는 인자와 함께 특정 화면으로 이동하거나, 백 스택과 현재 목적지를 관리하고, `NavHost` 안의 전체 내비게이션 동작을 제어합니다.

#### 2. 화면 사이 이동 {#navigating-between-screens}

`HomeScreen` 은 `DetailsScreen` 으로 이동하는 콜백을 받아 사용합니다.

```kotlin
@Composable
fun HomeScreen(
    onNavigateToDetails: () -> Unit
) {
    Column {
        Button(onClick = onNavigateToDetails) {
            Text(text = "Navigate to Details")
        }
    }
}
```
{title="HomeScreen.kt"}

`onNavigateToDetails` 람다를 파라미터로 받아 내비게이션 로직을 화면 코드와 분리합니다. 버튼 클릭 시 `navController.navigate(route = Details)` 가 호출되어 사용자가 `DetailsScreen` 으로 이동합니다.

Jetpack Compose Navigation 라이브러리는 트랜지션 애니메이션, [딥 링크](https://developer.android.com/develop/ui/compose/navigation#deeplinks), [type-safe routes](https://developer.android.com/guide/navigation/design/type-safety), [중첩 내비게이션](https://developer.android.com/develop/ui/compose/navigation#nested-nav), [테스트 전략](https://developer.android.com/develop/ui/compose/navigation#testing), [Hilt 통합](https://developer.android.com/training/dependency-injection/hilt-jetpack#viewmodel-navigation) 등 폭넓은 기능을 제공합니다. 또한 내비게이션 시스템 안에서 ViewModel 수명 주기를 효율적으로 관리해 주는 전용 viewModelStore도 제공합니다.

Kotlin Multiplatform(KMP)을 사용한다면 JetBrains가 [KMP 기반 내비게이션](https://www.jetbrains.com/help/kotlin-multiplatform-dev/compose-navigation-routing.html)을 지원하도록 Jetpack Compose Navigation 라이브러리를 포크해 제공하므로, 멀티 플랫폼에서도 같은 패턴을 그대로 활용할 수 있습니다.

### 요약 {#summary}

<tldr>

내비게이션은 모던 Android 개발에서 빠질 수 없는 기능입니다. 직접 구현도 가능하지만, 딥 링크, type-safe 라우트, Hilt 통합, ViewModel 수명 주기 관리 같은 고급 기능까지 함께 다루려면 Jetpack Compose Navigation 라이브러리를 사용하는 편이 권장됩니다. Google의 [Now in Android](https://github.com/android/nowinandroid) 프로젝트에서 베스트 프랙티스 형태의 구현을 살펴볼 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Navigation 라이브러리 없이 다중 화면 Compose 앱에서 화면 이동과 화면 상태 보존을 어떻게 관리하시겠습니까?">

가장 자연스러운 접근은 **현재 화면을 표현하는 sealed type 의 상태를 ViewModel 에 두고, 그 상태에 따라 컴포저블을 분기하는 구조** 를 만드는 것입니다. ViewModel 측에 `currentScreen: StateFlow&lt;Screen&gt;` 같은 상태를 두고, 화면 측에서는 `when (screen) { is Home -> HomeScreen(...) is Details -> DetailsScreen(...) }` 형태로 분기합니다. 백 스택 동작이 필요하다면 `ArrayDeque&lt;Screen&gt;` 같은 단순 자료구조를 ViewModel 안에서 관리하고, push/pop 메서드로 상태를 갱신하는 식으로 직접 다룰 수 있습니다.

화면별 상태 보존은 `SaveableStateHolder` 와 `rememberSaveable` 의 조합이 핵심입니다. 본문 예시처럼 `SaveableStateHolder.SaveableStateProvider(currentScreen) { ... }` 으로 화면을 감싸 두면, 화면 키별로 그 안에서 사용된 `rememberSaveable` 값들이 자동으로 저장·복원됩니다. 이 덕분에 사용자가 다른 화면으로 이동했다가 돌아와도 이전 입력이나 스크롤 위치, 펼침/접힘 상태가 그대로 유지됩니다. 더 이상 보여 줄 일이 없는 화면의 상태는 `saveableStateHolder.removeState(key)` 로 명시적으로 정리해 메모리를 통제합니다.

다만 이 방식은 작은 앱에서 잘 동작하지만, 화면 수가 늘면 빠르게 한계에 부딪힙니다. 딥 링크, 트랜지션 애니메이션, type-safe 인자 전달, ViewModel 수명 주기 관리, 시스템 백 버튼 처리 같은 부분은 직접 구현하면 검증 비용이 매우 큽니다. 그래서 실무에서는 화면이 두세 개 이상으로 늘어나는 시점에 Jetpack Compose Navigation 으로 전환하는 편이 일반적입니다. 학습 목적으로 한 번 직접 만들어 보고 그 한계를 체감한 뒤, 라이브러리로 옮겨 가는 흐름이 가장 자연스럽습니다.

</def>
<def title="Q) Jetpack Compose Navigation에서 NavHost와 NavController 시스템은 백 스택과 ViewModel 수명 주기를 어떻게 다루나요?">

`NavHost` 는 컴포저블 화면들을 라우트와 매핑한 **그래프** 이고, `NavController` 는 그 그래프 위에서 백 스택과 현재 목적지를 관리하는 **컨트롤러** 입니다. 사용자가 `navController.navigate(...)` 를 호출하면 새 백 스택 엔트리가 push 되고, 시스템 백 키 또는 `popBackStack()` 호출 시 가장 위 엔트리가 pop 됩니다. 각 백 스택 엔트리는 단순한 라우트 정보가 아니라 그 화면이 가졌던 상태와 인자, 그리고 그 화면의 ViewModel 까지 함께 묶어 두는 단위라는 점이 핵심입니다.

ViewModel 수명 주기는 백 스택 엔트리에 종속됩니다. `NavBackStackEntry` 자체가 `ViewModelStoreOwner` 를 구현하고 있어, `viewModel&lt;MyVm&gt;()` 또는 `hiltViewModel()` 을 그 화면에서 호출하면 그 백 스택 엔트리에 묶인 ViewModelStore 안에서 인스턴스가 만들어집니다. 그 결과 같은 화면을 다시 컴포지션해도 같은 ViewModel 이 재사용되고, 그 화면이 백 스택에서 pop 될 때 비로소 ViewModel 의 `onCleared()` 가 호출됩니다. 즉 ViewModel 의 생사가 **화면 단위 백 스택 엔트리** 와 정확히 일치하기 때문에, 화면 회전이나 임시 컴포지션 복귀에서도 상태가 안전하게 유지됩니다.

여기에 더해 Compose Navigation 은 두 가지 추가 도구를 제공합니다. 첫째, **shared ViewModel** 이 필요한 자리(예: 같은 그래프 안 여러 화면이 같은 데이터를 공유) 에서는 `navController.getBackStackEntry(parentRoute)` 를 통해 부모 엔트리의 store 를 가져와 ViewModel 을 공유할 수 있습니다. 둘째, 화면 트랜지션 동안의 상태도 `NavBackStackEntry.savedStateHandle` 로 안전하게 관리할 수 있어, 한 화면에서 결과를 다른 화면으로 돌려보내는 패턴(예: 선택 다이얼로그 결과 반환)을 깔끔하게 구현할 수 있습니다. 이 두 가지가 결합되어, 라이브러리를 사용하는 것만으로 백 스택과 ViewModel 수명을 일관되게 다룰 수 있습니다.

</def>
</deflist>

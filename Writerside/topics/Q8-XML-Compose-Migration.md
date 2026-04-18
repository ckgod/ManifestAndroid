# Q8) XML → Jetpack Compose 마이그레이션 전략

## XML 기반 프로젝트를 Jetpack Compose로 어떻게 마이그레이션하나요? {#how-to-migrate}

XML 기반 UI에서 Jetpack Compose로 옮겨 가는 작업은 앱을 현대화하고 UI 개발을 단순화할 수 있는 좋은 기회입니다. 다만 이 마이그레이션은 영향 범위를 작게 유지하기 위한 신중한 계획과 실행이 필요합니다. 다음은 공식 가이드와 모범 사례를 토대로 정리한 핵심 전략들입니다.

### 1. 점진적(Incremental) 마이그레이션 {#incremental-migration}

점진적 마이그레이션은 Compose를 단계적으로 도입해 같은 프로젝트 안에서 XML과 Compose가 공존하도록 하는 방식입니다.

- **XML 안에 Compose 끼워 넣기**: 기존 XML 레이아웃에 `ComposeView` 를 두어 그 안에서 컴포저블을 띄울 수 있습니다. XML 기반 화면의 특정 영역만 Compose 로 강화하고 싶을 때 유용합니다.

```xml
<androidx.compose.ui.platform.ComposeView
    android:id="@+id/compose_view"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
```
{title="EmbedComposeInXmlLayout.xml"}

```kotlin
findViewById<ComposeView>(R.id.compose_view).setContent {
    Greeting("Hello Compose!")
}
```
{title="SetContentForComposeView.kt"}

- **Compose 안에 XML 끼워 넣기**: `AndroidView` 를 사용하면 컴포저블 안에서 XML 기반 View 를 띄울 수 있습니다. 마이그레이션 도중 레거시 컴포넌트의 동작을 그대로 유지해야 할 때 유용합니다.

```kotlin
@Composable
fun LegacyViewComposable() {
    AndroidView(factory = { context ->
        LayoutInflater.from(context).inflate(R.layout.legacy_view, null)
    })
}
```
{title="EmbedXmlInCompose.kt"}

이 전략은 마이그레이션을 통제 가능한 단위로 나누고 기존 기능이 깨질 위험을 최소화합니다.

### 2. 화면 단위(Screen-by-Screen) 마이그레이션 {#screen-by-screen}

실용적인 또 다른 전략은 한 화면씩 마이그레이션하는 것입니다. 비교적 단순하거나 현대화 효과가 가장 큰 화면부터 시작하는 편이 좋습니다.

1. Compose의 장점이 즉시 드러날 만한 화면을 식별합니다(예: 동적 레이아웃, 복잡한 애니메이션).
2. 해당 화면을 Compose로 완전히 다시 작성합니다.
3. XML 레이아웃을 컴포저블 함수로 대체하면서 Compose의 상태 주도 아키텍처를 활용합니다.

이 전략은 특정 기능에 집중하면서 점진적으로 Compose에 익숙해질 수 있게 해 줍니다. 화면 단위로 목표가 명확하므로("이 화면을 완전히 Compose로 옮긴다") 작업의 시작과 마무리도 분명해집니다.

### 3. 컴포넌트 단위(Component-by-Component) 마이그레이션 {#component-by-component}

화면 전체 대신 재사용 가능한 컴포넌트나 디자인 시스템을 단위로 마이그레이션하는 방법도 있습니다. 텍스트, 버튼, 또는 커스텀 컴포넌트가 좋은 시작 후보입니다.

1. 자주 쓰이는 UI 컴포넌트나 디자인 시스템의 일부를 식별합니다.
2. 그 컴포넌트들을 컴포저블 함수로 다시 만듭니다.
3. 앱 안에서 XML 등가물 자리에 새 컴포저블 컴포넌트를 끼워 넣습니다.

이 방식은 한 화면을 **부분적으로** 마이그레이션하면서 디자인 시스템을 점진적으로 다시 구현하는 흐름을 만들어 줍니다. 여러 화면에서 공유되는 UI 컴포넌트의 일관성을 유지하고 마이그레이션 작업량을 분산시키는 효과가 있습니다.

### 4. 전면 재작성(Full Rewrite) {#full-rewrite}

규모가 매우 크거나 Compose-first 로 전환하려는 프로젝트라면 전면 재작성이 가장 적합한 전략이 될 수 있습니다.

1. 테마, 레이아웃, 커스텀 컴포넌트를 Compose로 다시 만듭니다.
2. XML을 완전히 걷어내고 UI 스택 전체를 Compose로 옮깁니다.
3. 필요하다면 앱 아키텍처도 새로 정의해 Compose에 최적화된 모던 패턴(MVI, MVVM 등)을 채택합니다.

이 경우 개발 조직은 **상당한 시간과 자원** 을 투입해야 하고, QA 팀과 함께 철저한 **테스트와 검증** 단계를 거쳐야 합니다. 매끄러운 마이그레이션을 위해서는 잘 짜인 마이그레이션 계획이 필수이며, 팀이 Compose에 충분히 익숙하지 않다면 회귀 가능성이 커지므로 더더욱 신중한 계획이 필요합니다.

### 5. 라이브러리에서의 호환성 활용 {#interoperability-for-libraries}

Compose의 호환성(interoperability)은 아직 Compose에 대응하지 않은 라이브러리까지 포괄합니다. [ComposeView](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/compose-in-views) 또는 [AndroidView](https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/views-in-compose)를 활용하면 라이브러리가 제공하는 UI 컴포넌트를 그대로 사용하면서 다른 부분은 Compose로 옮겨 갈 수 있습니다.

### 6. 마이그레이션 중에도 테스트와 모니터링 {#test-during-migration}

마이그레이션 중에 앱이 기대대로 동작하는지 확인하기 위해 테스트는 필수입니다. [Compose 테스트 라이브러리](https://developer.android.com/develop/ui/compose/testing)로 새 컴포저블을 검증하고, 함께 **성능 프로파일링** 을 수행해 Compose 구현이 기존 XML 구현 대비 동등하거나 더 좋은 사용자 경험을 제공하는지 확인하는 것이 좋습니다.

### 요약 {#summary}

<tldr>

Jetpack Compose 마이그레이션은 점진적으로 진행할 수도 있고 전면 재작성으로 진행할 수도 있으며, 프로젝트의 범위와 목표에 맞춰 선택해야 합니다. Compose는 XML과의 호환성(interoperability)을 통해 두 방식이 공존할 수 있게 해 주므로 매끄러운 전환이 가능합니다. 컴포넌트 단위든 화면 단위든, 핵심은 위험은 줄이면서 Compose가 제공하는 유지보수성·확장성·모던한 UI 경험의 이점을 최대한 끌어내는 전략을 선택하는 일입니다. 더 깊이 있는 자료는 *Migration strategy*, *Migrating Sunflower to Jetpack Compose*, *Migrating to Jetpack Compose — an interop love story* 시리즈를 참고할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) XML에서 Compose로 마이그레이션할 때, 기존 View 기반 레이아웃 안에 컴포저블을 어떻게 통합하며, 어떤 상황에서 이 접근이 가장 유용한가요?">

기존 View 레이아웃 안에 컴포저블을 통합하는 표준 방식은 XML 안에 `<androidx.compose.ui.platform.ComposeView>` 를 두고, 코드에서 그 ComposeView 를 찾아 `setContent { ... }` 로 컴포저블을 붙이는 것입니다. ComposeView 는 평범한 View 처럼 동작하면서 그 안에 자체 Composition 을 만들기 때문에, 화면의 일부만 Compose로 그리는 형태가 자연스럽게 만들어집니다. 동일 화면 안에서 일부 영역은 기존 XML 위젯 그대로, 다른 영역은 Compose로 다루는 구성이 가능합니다.

이 접근이 가장 빛을 발하는 시점은 **점진적 마이그레이션의 초기 단계** 와 **재사용 가능한 디자인 시스템 컴포넌트를 먼저 옮기는 단계** 입니다. 화면 전체를 한꺼번에 다시 만들기에는 부담이 크지만, 자주 변경되는 영역(예: 카드 리스트의 셀, 새로 추가되는 위젯, 공통 헤더)만 ComposeView 로 갈아치우면 변화가 작은 만큼 회귀 위험도 작아집니다. RecyclerView 의 ViewHolder 안에서 ComposeView 를 사용해 셀 단위로 Compose를 도입하는 패턴도 흔합니다.

다만 한 화면에 ComposeView 를 너무 잘게 흩어 두면 각자 자체 Composition 을 가지므로 상태 공유와 측정/레이아웃 비용이 늘어납니다. 그래서 가능한 한 의미 있는 영역 단위(예: 한 섹션 전체, 한 다이얼로그 전체)로 묶어 두는 것이 좋습니다. 반대 방향의 통합 — 컴포저블 안에서 기존 View 를 띄워야 할 때 — 은 `AndroidView` 가 짝꿍 역할을 합니다. 이 두 다리(`ComposeView`/`AndroidView`)를 함께 활용하면 양방향 호환을 통해 마이그레이션 단계마다 가장 비용이 적은 길을 선택할 수 있습니다.

</def>
<def title="Q) 화면 단위 마이그레이션과 컴포넌트 단위 마이그레이션 각각의 장단점은 무엇인가요?">

화면 단위 마이그레이션의 장점은 **목표가 분명하다** 는 점입니다. "이 화면을 완전히 Compose로 옮긴다" 가 작업 단위이므로 시작과 종료가 명확하고, 한 화면이 끝났을 때 Compose의 효용을 통째로 체험할 수 있습니다. 동적인 레이아웃이나 복잡한 애니메이션처럼 Compose의 장점이 두드러지는 화면을 먼저 잡으면 팀의 학습 곡선도 빠르게 올라옵니다. 단점은 **공통 컴포넌트가 정리되지 않은 상태에서 화면을 전부 다시 그리게 된다** 는 점입니다. 비슷한 카드 위젯이 화면마다 따로 만들어지다 보면 디자인 시스템이 분산되고, 다음 화면을 옮길 때 마이그레이션 비용이 크게 줄지 않습니다.

컴포넌트 단위 마이그레이션은 정확히 그 반대의 무게중심을 가집니다. **재사용 단위를 먼저 정리** 하므로 한 번 만든 컴포저블이 여러 화면에서 동시에 쓰이기 시작하고, 디자인 시스템의 일관성이 유지됩니다. 디자인 시스템 컴포넌트가 어느 정도 갖춰지면 그 다음의 화면 마이그레이션은 훨씬 빠르게 진행됩니다. 단점은 **사용자에게 보이는 변화가 한참 뒤에야 나타난다** 는 점입니다. 컴포넌트 라이브러리 작업이 길어지는 동안 기획이나 디자인은 화면 자체의 개선을 기다려야 할 수 있고, 그 사이 우선순위가 흔들리면 작업이 흐지부지될 위험이 있습니다.

실무에서는 두 전략이 단독으로 쓰이기보다 **혼합 전략** 으로 정착하는 경우가 많습니다. 즉 디자인 시스템의 핵심 컴포넌트(버튼, 카드, 인풋, 토스트 정도)는 컴포넌트 단위로 먼저 옮겨 두고, 그 위에서 새로 만드는 화면이나 마이그레이션 우선순위가 높은 화면은 화면 단위로 옮기는 식입니다. 이 조합이 사용자에게 보이는 변화를 끌고 가면서도 공통 컴포넌트의 분산을 막아 주어, 장기적인 비용이 가장 작아지는 경향이 있습니다.

</def>
</deflist>

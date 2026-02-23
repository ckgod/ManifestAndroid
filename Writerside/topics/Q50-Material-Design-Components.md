# Q50) Material Design Components

## Material Design Components(MDC)란 무엇인가요? {#what-is-mdc}

Material Design Components(MDC)는 Google의 Material Design 가이드라인을 기반으로 한 커스터마이징 가능한 UI 위젯 및 도구 모음입니다. 일관되고 사용자 친화적인 인터페이스를 제공하면서도, 앱의 브랜딩과 디자인 요구에 맞게 외형과 동작을 자유롭게 커스터마이징할 수 있습니다. MDC는 Material Components for Android(MDC-Android) 라이브러리의 일부로, Android 프로젝트에 원활하게 통합되어 최신 디자인 원칙을 효과적으로 구현할 수 있게 해줍니다.

### 주요 기능 {#key-features}

**Material 테마**

MDC는 Material Theming을 통해 타이포그래피, 도형, 색상을 전역 또는 컴포넌트 단위로 커스터마이징할 수 있습니다. 앱 전체에서 일관성을 유지하면서 브랜드 아이덴티티에 맞게 UI를 쉽게 조정할 수 있습니다.

**사전 구축된 UI 컴포넌트**

버튼, 카드, 앱 바, 내비게이션 드로어, 칩 등 다양한 즉시 사용 가능한 UI 컴포넌트를 제공합니다. 이 컴포넌트들은 접근성, 성능, 반응성에 최적화되어 있습니다.

**애니메이션 지원**

Material Design은 모션과 전환을 강조합니다. MDC는 공유 요소 전환, 리플 효과, 시각적 피드백 같은 내장 애니메이션 지원을 포함하여 사용자 상호작용을 풍부하게 만들어 줍니다.

**다크 모드 지원**

라이트 모드와 다크 모드에 대한 테마를 정의하면서도 시각적 일관성을 보장하는 다크 모드 구현 도구를 제공합니다.

**접근성**

MDC는 접근성 표준을 준수하여 더 넓은 터치 영역, 시맨틱 레이블, 올바른 포커스 관리 등의 기능을 제공합니다.

### MaterialButton 사용 예시 {#material-button-example}

```xml
<com.google.android.material.button.MaterialButton
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Click Me"
    app:cornerRadius="8dp"
    app:icon="@drawable/ic_example"
    app:iconGravity="start"
    app:iconPadding="8dp" />
```
{title="MaterialButtonExample.xml"}

`MaterialButton`은 모서리 반경, 아이콘, 패딩 등을 XML 속성으로 쉽게 커스터마이징하여 Material Design 원칙에 맞는 버튼을 만들 수 있습니다.

### 요약 {#summary}

<tldr>
Material Design Components(MDC)는 Google의 Material Design 가이드라인을 따르는 현대적이고 일관된 UI를 만들 수 있게 해줍니다. 테마, 사전 구축된 위젯, 애니메이션 지원, 접근성 도구를 통해 다양한 기기와 화면 크기에서 고품질 UI를 구현하는 과정을 단순화합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) MDC의 Material Theming이 앱 전체의 디자인 일관성 유지에 어떻게 도움이 되나요?">

Material Theming은 색상, 타이포그래피, 도형이라는 세 가지 핵심 축을 중심으로 앱 전체 스타일을 중앙에서 관리할 수 있게 해줍니다.

**테마 정의 예시:**

```xml
<style name="Theme.MyApp" parent="Theme.MaterialComponents.DayNight">
    <!-- 색상 팔레트 -->
    <item name="colorPrimary">@color/purple_500</item>
    <item name="colorSecondary">@color/teal_200</item>
    <!-- 타이포그래피 -->
    <item name="textAppearanceBody1">@style/TextAppearance.MyApp.Body1</item>
    <!-- 도형 -->
    <item name="shapeAppearanceSmallComponent">@style/ShapeAppearance.MyApp.Small</item>
</style>
```

이 테마를 한 곳에서 정의하면 모든 MDC 컴포넌트(버튼, 카드, 텍스트 필드 등)가 자동으로 해당 스타일을 반영합니다. 브랜드 색상을 변경하거나 디자인 시스템을 업데이트할 때 개별 컴포넌트를 하나하나 수정하지 않고 테마만 변경하면 앱 전체에 일관되게 적용됩니다.

</def>
</deflist>

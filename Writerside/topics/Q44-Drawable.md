# Q44) Drawable

## Drawable이란 무엇이며, UI 개발에서 어떻게 사용되나요? {#what-is-drawable}

Drawable은 화면에 그릴 수 있는 모든 것에 대한 일반적인 추상화 개념입니다. 이미지, 벡터 그래픽, 도형 기반 요소 등 다양한 유형의 그래픽 콘텐츠를 위한 기본 클래스 역할을 하며, 배경, 버튼, 아이콘, 커스텀 뷰 등 UI 컴포넌트에서 널리 사용됩니다. Android는 각각의 특정 사용 사례를 위해 설계된 다양한 타입의 Drawable 객체를 제공합니다.

### BitmapDrawable (래스터 이미지) {#bitmap-drawable}

BitmapDrawable은 PNG, JPG, GIF와 같은 래스터 이미지를 표시하는 데 사용됩니다. 비트맵 이미지의 크기 조정, 타일링, 필터링을 지원하며, ImageView 컴포넌트에서 이미지를 표시하거나 배경으로 사용할 때 가장 일반적으로 활용됩니다.

```xml
<bitmap xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@drawable/sample_image"
    android:tileMode="repeat"/>
```
{title="bitmap_drawable.xml"}

BitmapDrawable은 사진이나 복잡한 이미지를 표시할 때 적합하지만, 다양한 화면 밀도에서 픽셀화가 발생할 수 있으므로 해상도별로 여러 버전의 이미지를 제공하는 것이 좋습니다.

### VectorDrawable (확장 가능한 벡터 그래픽) {#vector-drawable}

VectorDrawable은 XML 경로를 사용하여 SVG와 유사한 확장 가능한 벡터 그래픽을 나타냅니다. 비트맵과 달리 벡터는 어떤 해상도에서도 품질을 유지하므로, 다양한 화면 밀도를 가진 기기에서 픽셀화 문제를 피할 수 있어 아이콘, 로고, 확장 가능한 UI 요소에 이상적입니다.

```xml
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF0000"
        android:pathData="M12,2L15,8H9L12,2Z"/>
</vector>
```
{title="vector_drawable.xml"}

VectorDrawable은 파일 크기가 작고 모든 화면 밀도에서 선명하게 표시되므로, 최신 Android 앱 개발에서 비트맵 이미지를 대체하는 권장 방식입니다.

### NinePatchDrawable (패딩을 유지하는 크기 조정 가능한 이미지) {#nine-patch-drawable}

NinePatchDrawable은 특정 영역(예: 모서리나 패딩)을 보존하면서 크기를 조정할 수 있는 특수한 유형의 비트맵입니다. 채팅 말풍선이나 버튼과 같은 확장 가능한 UI 컴포넌트를 만드는 데 유용하며, Nine-patch 이미지(.9.png)는 늘어날 수 있는 영역과 고정된 영역을 정의하는 추가 1픽셀 테두리를 포함합니다.

```xml
<nine-patch xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@drawable/chat_bubble.9.png"/>
```
{title="nine_patch_drawable.xml"}

.9.png 파일을 만들려면 Android Studio의 NinePatch 도구를 사용하여 늘어날 수 있는 영역을 정의할 수 있습니다. 이 방식은 다양한 콘텐츠 크기에 맞춰 자연스럽게 확장되는 UI 요소를 디자인할 때 매우 효과적입니다.

### ShapeDrawable (커스텀 도형) {#shape-drawable}

ShapeDrawable은 XML로 정의되며 이미지를 사용하지 않고도 둥근 사각형, 타원형 또는 기타 단순한 도형을 만드는 데 사용할 수 있습니다. 버튼, 배경, 커스텀 UI 컴포넌트에 유용하며, 코드 변경만으로 색상, 크기, 모서리 반경 등을 쉽게 조정할 수 있습니다.

```xml
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#FF5733"/>
    <corners android:radius="8dp"/>
</shape>
```
{title="shape_drawable.xml"}

ShapeDrawable은 단순한 배경이나 구분선을 만들 때 이미지 파일 없이도 원하는 디자인을 구현할 수 있어 리소스 관리가 효율적입니다.

### LayerDrawable (여러 Drawable을 쌓은 구조) {#layer-drawable}

LayerDrawable은 여러 drawable을 하나의 레이어 구조로 결합하는 데 사용되며, 복잡한 UI 배경을 만들 때 유용합니다. 오버레이 효과나 쌓인 비주얼을 생성할 때 활용됩니다.

```xml
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <solid android:color="#000000"/>
        </shape>
    </item>
    <item android:drawable="@drawable/icon" android:top="10dp"/>
</layer-list>
```
{title="layer_drawable.xml"}

LayerDrawable을 사용하면 여러 레이어를 겹쳐서 그림자 효과, 테두리, 또는 복합적인 배경 디자인을 구현할 수 있습니다.

### Drawable 선택 가이드 {#drawable-selection-guide}

적절한 Drawable 타입을 선택하는 것은 사용 사례에 따라 달라집니다. 아이콘이나 로고처럼 확장성이 중요한 경우 VectorDrawable을 사용하고, 사진이나 복잡한 이미지는 BitmapDrawable을 사용합니다. 단순한 도형이나 배경은 ShapeDrawable로 충분하며, 다양한 크기에 맞춰 확장되는 버튼이나 컨테이너는 NinePatchDrawable이 적합합니다. 복합적인 디자인이 필요한 경우 LayerDrawable을 통해 여러 요소를 조합할 수 있습니다.

### 요약 {#summary}

Drawable 클래스는 Android에서 다양한 유형의 그래픽을 처리하는 유연한 방법을 제공합니다. 올바른 Drawable을 선택하는 것은 디자인 요구사항, 확장성, UI 복잡도와 같은 사용 사례에 따라 달라집니다. 이러한 다양한 drawable 타입을 활용하면 개발자는 Android 애플리케이션에서 최적화되고 시각적으로 매력적인 UI 컴포넌트를 만들 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 사용자 상호작용에 따라 도형과 색상이 동적으로 변하는 버튼의 배경을 Drawable만 사용하여 어떻게 만들 수 있나요?">

사용자 상호작용에 따라 동적으로 변하는 버튼 배경은 `StateListDrawable`(또는 XML에서 `<selector>`)을 사용하여 구현할 수 있습니다. StateListDrawable은 버튼의 상태(pressed, focused, enabled, disabled 등)에 따라 다른 drawable을 표시할 수 있게 해줍니다.

먼저, 각 상태에 대한 개별 drawable을 정의합니다. 예를 들어, 일반 상태와 눌렸을 때의 상태를 위한 두 개의 ShapeDrawable을 만들 수 있습니다.

```xml
<!-- res/drawable/button_normal.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#2196F3"/>
    <corners android:radius="8dp"/>
</shape>
```

```xml
<!-- res/drawable/button_pressed.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#1976D2"/>
    <corners android:radius="8dp"/>
</shape>
```

그런 다음, StateListDrawable을 사용하여 상태에 따라 다른 drawable을 적용합니다.

```xml
<!-- res/drawable/button_background.xml -->
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true" android:drawable="@drawable/button_pressed"/>
    <item android:state_focused="true" android:drawable="@drawable/button_pressed"/>
    <item android:drawable="@drawable/button_normal"/>
</selector>
```

이 button_background.xml 파일을 버튼의 배경으로 설정하면, 사용자가 버튼을 누르거나 포커스할 때 자동으로 배경이 변경됩니다.

```xml
<Button
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:background="@drawable/button_background"
    android:text="Click Me"/>
```

더 복잡한 효과를 원한다면 LayerDrawable을 StateListDrawable과 결합하여 그림자, 테두리, 그라데이션 등을 추가할 수 있습니다. 또한 AnimatedStateListDrawable을 사용하면 상태 전환 시 애니메이션 효과도 추가할 수 있습니다.

이 방식의 장점은 이미지 파일 없이 XML만으로 동적인 버튼을 구현할 수 있고, 색상이나 도형을 쉽게 변경할 수 있으며, 벡터 기반이므로 모든 화면 크기에서 선명하게 표시된다는 것입니다.

</def>
</deflist>

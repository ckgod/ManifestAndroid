# Q33) View Lifecycle

## View 생명주기에 대해 설명해보세요

Android에서 View 생명주기는 View(예: TextView 또는 Button)가 생성되고, `Activity`나 `Fragment`에 연결되고, 화면에 표시되며, 최종적으로 소멸되거나 분리될 때 겪는 생명주기 이벤트를 의미합니다. 

View 생명주기를 이해하는 것은 개발자가 View의 초기화, 렌더링, 해체를 관리하고, 사용자 작업, 시스템 이벤트에 응답하여 View 생명주기에 따라 커스텀 View를 구현하거나 적절한 시점에 리소스를 해제하는 데 도움이 됩니다.

![view-lifecycle.png](view-lifecycle.png)

1.  **View 생성 (onAttachedToWindow)**: View가 프로그래밍 방식으로 또는 XML 레이아웃을 통해 인스턴스화되는 단계입니다. 리스너 설정 및 데이터 바인딩과 같은 초기 설정 작업이 여기서 수행됩니다. `onAttachedToWindow()` 메서드는 View가 부모에 추가되고 화면에 렌더링될 준비가 되었을 때 호출됩니다.
2.  **레이아웃 단계 (onMeasure, onLayout)**: 이 단계에서 View의 크기와 위치가 계산됩니다. `onMeasure()` 메서드는 View의 레이아웃 매개변수와 부모 제약 조건에 따라 너비와 높이를 결정합니다. 측정된 후 `onLayout()` 메서드는 View를 부모 내에 배치하여 화면에 나타날 최종 위치를 확정합니다.
3.  **그리기 단계 (onDraw)**: 크기와 위치가 확정된 후, `onDraw()` 메서드는 텍스트나 이미지와 같은 View의 콘텐츠를 [Canvas](https://developer.android.com/reference/android/graphics/Canvas)에 렌더링합니다. 커스텀 View는 이 메서드를 재정의하여 커스텀 그리기 로직을 정의할 수 있습니다.
4.  **이벤트 처리 (onTouchEvent, onClick)**: 이 단계에서 인터랙티브 View는 터치 이벤트, 클릭, 제스처와 같은 사용자 상호작용을 처리합니다. `onTouchEvent()` 및 `onClick()`과 같은 메서드는 이러한 이벤트를 처리하고 사용자 입력에 대한 View의 응답을 정의하는 데 사용됩니다.
5.  **View 분리 (onDetachedFromWindow)**: View가 화면과 부모 ViewGroup에서 제거될 때(예: Activity 또는 Fragment 소멸 중), `onDetachedFromWindow()` 메서드가 호출됩니다. 이 단계는 리소스를 정리하거나 리스너를 분리하는 데 이상적입니다.
6.  **View 소멸**: View가 더 이상 사용되지 않으면 가비지 컬렉션됩니다. 개발자는 메모리 누수를 방지하고 성능을 최적화하기 위해 이벤트 리스너 또는 백그라운드 작업과 같은 모든 리소스가 올바르게 해제되었는지 확인해야 합니다.

### 요약

View의 생명주기는 생성, 측정, 레이아웃, 그리기, 이벤트 처리 및 최종 분리를 포함하며, Android 애플리케이션 내에서 표시되고 사용되는 동안 거치는 단계를 반영합니다. 
더 자세한 내용은 [Android 공식 문서](https://developer.android.com/develop/ui/views/layout/custom-views/custom-components)를 참조하세요.

#### Q1

> 이미지 로딩이나 애니메이션 설정과 같은 비용이 많이 드는 초기화 작업을 수행해야 하는 Custom View를 만들고 있습니다. View 생명주기의 어느 시점에서 이러한 리소스를 초기화해야 하며, 메모리 누수를 방지하기 위해 적절한 정리를 어떻게 보장할 수 있을까요?

##### A {collapsible="true" #A1}

Custom View에서 무거운 리소스(이미지, 애니메이션)을 다룰 때 가장 중요한 것은 **UI 스레드 차단 방지**와 **확실한 메모리 해제** 입니다.

**리소스 초기화 시점**
1. 기본 객체 할당
   * 시점: `constructor`(생성자) 또는 `init` 블록
   * 뷰가 생성될 때 한 번만 수행하면 되는 가벼운 객체들(`Paint`, `Matrix`, 기본 `ValueAnimator` 인스턴스)은 생성자에서 미리 만들어 두는 것이 좋습니다. `onDraw`에서 객체를 생성하면 메모리 릭과 버벅임의 주범이 됩니다.
2. 사이즈 의존 작업 (`Bitmap` 리사이징, 그라디언트 계산)
   * 시점: `onSizeChanged(w, h, oldw, oldh)`
   * 뷰의 크기가 확정된 직후에 호출됩니다. 뷰의 크기에 맞춰 비트맵을 생성하거나, 쉐이더를 계산해야한다면 이곳이 최적의 장소입니다. `onMeasure`나 `onLayout`은 여러 번 호출될 수 있어 비효율적입니다. 
3. 활성 리소스 시작 (애니메이션 시작, 리스너 등록)
   * 시점: `onAttachedToWindow()`
   * 뷰가 실제 윈도우에 붙어서 화면에 그려질 준비가 완료된 시점입니다. 애니메이션을 시작하거나, 센서/브로드캐스트 리시버를 등록하거나, 이미지 로딩 라이브러리(Glide/Coil) 요청을 시작하기 가장 안전한 시점입니다.

**리소스 정리 및 메모리 누수 방지**

1. 리소스 정리 
   * 시점: `onDetachedFromWindow()`
   * 뷰가 윈도우에서 떨어져 나가는 시점입니다. (Activity가 종료되거나, ViewGroup에서 removeView가 호출될 떄), 여기서 정리를 안 하면 뷰는 사라져도 백그라운드에서 애니메이션이 돌아가거나, 콜백이 호출되어 Context 릭이 발생합니다. 
   * 실행 중인 모든 `Animator` / `Handler` / `Runnable` 중지 및 제거
   * 등록된 리스너 해제
   * 진행 중인 비동기 작업 취소
   * 큰 비트맵 객체에 `null` 처리


#### Q2

>  애플리케이션에 동적으로 생성되는 `View`가 포함된 복잡한 `UI`가 있으며, 이로 인해 성능 문제가 발생합니다. 렌더링 효율성을 개선하고 응답성을 유지하기 위해 `onMeasure()` 및 `onLayout()` 메서드를 어떻게 최적화하시겠습니까?

##### A {collapsible="true" #A2}

동적으로 생성되는 복잡한 UI에서 `onMeasure()`와 `onLayout()`은 렌더링 성능의 핵심 병목 지점입니다. 이 두 메서드는 View 계층 구조를 순회하며 반복 호출되기 때문에, 최적화하지 않으면 UI 스레드를 차단하고 프레임 드롭(jank)을 발생시킵니다.

**onMeasure() 최적화**

1. **불필요한 측정 방지**
   * `MeasureSpec`을 확인하여 이전 측정값과 동일하면 재측정을 건너뜁니다.
   ```kotlin
   override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
       val widthMode = MeasureSpec.getMode(widthMeasureSpec)
       val widthSize = MeasureSpec.getSize(widthMeasureSpec)

       // 캐시된 측정값이 유효하면 재사용
       if (widthMode == MeasureSpec.EXACTLY &&
           widthSize == lastMeasuredWidth) {
           setMeasuredDimension(lastMeasuredWidth, lastMeasuredHeight)
           return
       }
       // ... 실제 측정 로직
   }
   ```

2. **자식 View 측정 최소화**
   * `GONE` 상태의 자식은 측정하지 않습니다.
   * `measureChildWithMargins()` 대신 `getChildMeasureSpec()`을 직접 사용하여 불필요한 계산을 줄입니다.
   * 자식 View가 많다면, 변경된 자식만 재측정합니다.

3. **복잡한 계산 캐싱**
   * 측정 과정에서 필요한 복잡한 계산(텍스트 너비, 이미지 비율)은 결과를 캐싱합니다.
   * `requestLayout()`이 호출되지 않았다면 캐시된 값을 재사용합니다.

**onLayout() 최적화**

1. **불필요한 레이아웃 방지**
   * 위치가 변경되지 않았다면 자식의 `layout()`을 호출하지 않습니다.
   ```kotlin
   override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
       if (!changed && !needsRelayout) {
           return // 레이아웃 변경이 없으면 스킵
       }

       var childTop = paddingTop
       for (i in 0 until childCount) {
           val child = getChildAt(i)
           if (child.visibility == GONE) continue

           val childHeight = child.measuredHeight
           // 이전 위치와 동일하면 스킵
           if (child.top != childTop || child.left != paddingLeft) {
               child.layout(paddingLeft, childTop,
                          paddingLeft + child.measuredWidth,
                          childTop + childHeight)
           }
           childTop += childHeight
       }
   }
   ```

2. **평탄한 계층 구조 유지**
   * 중첩된 `LinearLayout`이나 `RelativeLayout` 대신 `ConstraintLayout`을 사용하여 레이아웃 깊이를 줄입니다.
   * 깊이가 깊을수록 측정/레이아웃이 여러 번 수행되어 성능이 저하됩니다.

3. **좌표 계산 최적화**
   * 반복문 내에서 `getWidth()`, `getHeight()` 호출을 피하고, 변수에 미리 저장합니다.
   * 불필요한 `Rect` 객체 생성을 피하고 재사용합니다.
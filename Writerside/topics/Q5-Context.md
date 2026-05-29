# Q5) Context

## Context란 무엇인가요? 어떤 유형이 있나요?
Context는 애플리케이션의 환경 또는 상태를 나타내며 애플리케이션 별 리소스 및 클래스에 대한 액세스를 제공한다.
Context는 **앱과 안드로이드 시스템 사이의 다리 역할**을 하여 컴포넌트가 리소스, 데이터베이스, 시스템 서비스 등에 액세스 할 수 있도록 한다.
Context는 Activity Start, assets Access, layout inflate과 같은 작업에 필수적이다.

안드로이드에는 여러 유형의 Context가 있다. 

## Application Context
Application Context는 애플리케이션의 라이프사이클에 연결된다. 
현재 Activity 또는 Fragment와 독립적인 수명이 긴 전역 Context가 필요할 때 사용된다. 
이 Context는 `getApplicationContext()`를 호출하여 받아올 수 있다.

### Application Context 사용 사례 {#usage-application-context}
- `SharedPreferences` 또는 데이터베이스와 같은 애플리케이션 전체 리소스에 액세스
- 전체 앱 수명 주기 동안 지속되어야 하는 Broadcast Receiver 등록
- 앱 수명 주기 전반에 걸쳐 존재하는 라이브러리 또는 컴포넌트를 초기화

## Activity Context
Activity Context(Activity의 인스턴스)는 Activity의 라이프사이클에 연결된다. 
리소스에 액세스하고, 다른 Activity를 시작하고, Activity와 관련된 layout을 inflate하는 데 사용된다.

### Activity Context 사용 사례 {#usage-activity-context}
- UI 컴포넌트 생성 및 수정
- 다른 Activity 시작
- 현재 Activity 범위 내 리소스, 테마에 액세스

## Service Context
Service Context는 Service의 라이프 사이클과 관련이 있다. 
주로 네트워크 작업을 수행하거나 음악을 재생하는 등 백그라운드에서 실행되는 작업에 사용된다.
Service에 필요한 시스템 수준의 서비스에 액세스할 수 있다.

## Broadcast Context
Broadcast Context는 Broadcast Receiver가 호출될 때 제공된다. 
수명이 짧으며 일반적으로 특정 Broadcast에 응답하는 데 사용된다. 
이 Context로는 장기간 실행되는 작업 수행에 사용하면 안된다.

## Context의 일반적인 사용 사례 {#common-usage-context}
1. Accessing Resources: Context는 strings, drawables, dimens 등 리소스에 대한 액세스를 `getString()`, `getDrawable()`과 같은 메서드를 사용하여 제공한다.
2. Inflating Layouts: layout inflater 를 사용하여 XML 레이아웃을 View로 inflate 한다.
3. Starting Activities and Services: Activity, Service 시작에 context가 필요하다.
4. Accessing System Services: Context는 `ClipboardManager`, `ConnectivityManager`와 같은 시스템 수준에 액세스할 수 있는 메서드를 제공한다.
5. Database and SharedPreferences Access: `SQLite` 데이터베이스 또는 `SharedPreferences`와 같은 저장소 메커니즘에 액세스할 수 있다.

## 요약
Context는 안드로이드 핵심 구성 요소로, **앱과 시스템 간의 상호 작용**을 가능하게 한다.
Application Context, Activity Context, Service Context 등 다양한 유형의 컨텍스트가 존재하고 고유한 용도로 사용된다.
Context를 올바르게 사용하면 리소스를 효율적으로 관리하고 메모리 누수나 크래시를 방지할 수 있으므로 올바른 Context를 선택하고 불필요하게 유지하지 않는 것이 중요하다.


<deflist collapsible="true" default-state="collapsed">
<def title="Q) 안드로이드 애플리케이션에서 올바른 유형의 컨텍스트를 사용하는 것이 중요한 이유?">

Context마다 **수명(생명주기)과 가진 능력이 다르기** 때문입니다. 잘못된 Context를 쓰면 메모리 누수나 크래시로 이어집니다.

- **수명 불일치로 인한 누수**: 화면 하나보다 오래 사는 객체(싱글톤, 정적 필드 등)가 Activity Context를 붙들고 있으면, Activity가 파괴돼도 GC가 회수하지 못해 메모리 누수가 생깁니다. 이런 경우에는 앱 전체와 수명을 같이하는 Application Context를 써야 합니다.
- **능력 차이**: 반대로 UI 작업(다이얼로그 표시, 테마가 적용된 뷰 inflate 등)에는 Application Context를 쓰면 안 됩니다. Application Context에는 화면(테마·윈도우) 정보가 없어 `BadTokenException` 등이 발생할 수 있고, 이때는 Activity Context가 필요합니다.

즉 "오래 살아야 하는 작업에는 Application Context, 화면·UI에 묶인 작업에는 Activity Context"라는 원칙에 따라, 작업의 수명과 성격에 맞는 Context를 선택하는 것이 중요합니다.

</def>
<def title="Q) Activity Context에 대한 참조를 오래 보유할 경우 발생할 수 있는 잠재적 위험?">

가장 큰 위험은 **메모리 누수**입니다. Activity Context는 사실상 Activity 인스턴스 자체이고, Activity는 그 안의 View 계층·리소스를 모두 참조합니다. 따라서 Activity보다 오래 사는 객체가 이 Context를 붙들고 있으면, Activity가 `onDestroy()`된 뒤에도 GC가 Activity와 그에 딸린 View·리소스 전체를 회수하지 못합니다.

대표적인 경로는 싱글톤·정적 필드에 Activity Context를 저장하거나, 백그라운드 작업·콜백·익명 내부 클래스가 Activity를 암묵적으로 캡처한 채 Activity 수명보다 오래 살아남는 경우입니다.

이런 누수가 쌓이면 화면을 회전하거나 재진입할 때마다 파괴됐어야 할 Activity가 메모리에 남아 사용량이 계속 늘고, 결국 `OutOfMemoryError`로 크래시할 수 있습니다. 그래서 수명이 긴 객체에는 Application Context를 사용하고, 불가피하게 Activity Context를 참조해야 한다면 `WeakReference`를 쓰거나 생명주기 종료 시점에 참조를 명시적으로 해제해야 합니다.

</def>
</deflist>
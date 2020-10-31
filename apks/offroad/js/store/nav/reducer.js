import { StackNavigator } from '../../navigators/StackNavigator';
import Logging from '../../native/Logging';

const getCurrentRouteName = (state) => {
  const route = state.routes[state.index];
  return typeof route.index === 'undefined' ? route.routeName : getCurrentRouteName(route);
}

export default (state, action) => {
  const nextState = StackNavigator.router.getStateForAction(action, state);

  // prevents navigating twice to the same route
 if (state && nextState) {
    const stateRouteName = getCurrentRouteName(state);
    const nextStateRouteName = getCurrentRouteName(nextState);

    if (stateRouteName !== nextStateRouteName) {
      // cloudLog when navigating to a new screen
      requestAnimationFrame(() => {
        Logging.cloudLog('Navigate to ' + nextStateRouteName, {
          to: nextStateRouteName,
          from: stateRouteName
        });
      });
    }

    return stateRouteName === nextStateRouteName ? state : nextState;
  }

  // Simply return the original `state` if `nextState` is null or undefined.
  return nextState || state;
};

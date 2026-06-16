import { Routes } from '@angular/router';
import {CreateAccountComponent} from './account/create_account';
import {LoginComponent} from './account/login';
import PlayerDashboard from './user/playerDashboard';


export const routes: Routes = [
  { path: 'create-account', component: CreateAccountComponent }, // Home/Login page
  { path: 'login', component: LoginComponent },
  { path: '',redirectTo: '/login',pathMatch : 'full' },
  { path: 'player-dashboard', component: PlayerDashboard },
  { path: '**', redirectTo: '/login' }
];

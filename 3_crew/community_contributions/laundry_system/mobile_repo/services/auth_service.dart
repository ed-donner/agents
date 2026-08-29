import 'api_service.dart';
import '../models/user.dart';

class AuthService {
  final ApiService _apiService = ApiService();
  User? _user;

  Future<User> login(String email, String password) async {
    _user = await _apiService.login(email, password);
    return _user!;
  }

  Future<User> register(String email, String password) async {
    _user = await _apiService.register(email, password);
    return _user!;
  }

  bool get isAuthenticated => _user != null;
}